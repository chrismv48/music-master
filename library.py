"""Docstring goes here"""
import os
import re
import urllib
import time
from datetime import timedelta, datetime

from lxml import etree
import acoustid

from EasyID3Patched import EasyID3Patched
from config import LOGGER, TRACK_DIRECTORY
from enricher import acoustid_lookup, search_echonest_for_song, search_echonest_artist_terms
from models.models import session, SavedTrack, Genre
from utils import clean_search_term, get_track_paths


def clean_genre(genre):
    return re.sub('[\W_]+', ' ', genre).lower()


class Track(object):
    def __init__(self, path):
        self.data = {}

        self.path = path
        print self.path
        self.easyID3 = EasyID3Patched(self.path)
        self.fingerprint = self.easyID3.get('acoustid_fingerprint')
        self.acquire_track_model()
        self.generate_attributes()

        def __repr__(self):
            if all([self.artist, self.title]):
                return '<' + self.artist + ' - ' + self.title + '>'
            else:
                return '<' + self.path + '>'

    def __setattr__(self, key, value):
        if key != 'data' and key in self.data.keys():
            # self.easyID3.update_from_dict({key: value})
            # self.model.from_dict({key: value})
            self.data[key] = value
        super(Track, self).__setattr__(key, value)

    @property
    def search_phrase(self):
        return clean_search_term(self.album_artist + ' ' + self.title if all([self.album_artist, self.title]) else
                                 self.path)

    def generate_attributes(self):
        for k, v in self.model.as_dict().iteritems():
            self.__setattr__(k, v)
            self.data[k] = v

        for k, v in self.easyID3.model_dict.iteritems():
            self.__setattr__(k, v)
            self.data[k] = v

    def acquire_track_model(self):
        # determine if fingerprint present, if not generate
        if not self.fingerprint:
            self.query_fingerprint()
        # use fingerprint to query model
        self.model = session.query(SavedTrack).get(self.fingerprint)
        # if 0 results, create model
        if not self.model:
            LOGGER.info('Track not found in database; creating...')
            self.model = SavedTrack()

    def query_fingerprint(self):
        self.duration, self.fingerprint = acoustid.fingerprint_file(self.path, 30)

    def enrich(self):
        if not self.last_searched_acoustid or self.last_searched_acoustid < (
                    self.last_searched_acoustid - timedelta(days=7)):
            LOGGER.info('Doing AcoustID lookup for track artist, title and album...')
            acoustid_data = acoustid_lookup(self.fingerprint, self.duration)
            self.data.update(acoustid_data)
            self.last_searched_acoustid = datetime.now()


        # TODO: submit to be analyzed if not found
        if self.last_searched_echonest and self.last_searched_echonest > (
                    self.last_searched_echonest - timedelta(days=7)):
            LOGGER.info('Track already enriched, skipping enrichment process.')
            return self

        LOGGER.info('Searching Echonest for track using: {}'.format(self.search_phrase))
        top_score_result = search_echonest_for_song(self.search_phrase)
        if top_score_result:
            LOGGER.info('Song found on Echonest: {} - {}'.format(top_score_result.artist_name,
                                                                 top_score_result.title))
            audio_summary = top_score_result.get_audio_summary()
            track_artist = top_score_result.artist_name.encode('utf-8')
            track_title = top_score_result.title.encode('utf-8')
            audio_summary['artist'] = track_artist
            audio_summary['title'] = track_title
            audio_summary = {k: v * 100 if v and v < 1 else v for k, v in
                             audio_summary.iteritems()}  # SQLAlchemy converts
            # values less than 1 to 0 before the validators can act.
            self.data.update(audio_summary)
            time.sleep(2)
        else:
            LOGGER.info('Track not found in Echonest')
        if not self.genres and (self.album_artist or self.artist):
            LOGGER.info('Searching Echonest for genres using artist {}'.format(self.album_artist or
                                                                               self.artist))
            top_term = search_echonest_artist_terms(self.album_artist or self.artist)
            if top_term:
                self.genres = top_term.title()
                LOGGER.info('Genre found: {}'.format(top_term))

            time.sleep(2)

        self.last_searched_echonest = datetime.now()
        self.meta_genre = self.match_meta_genre(self.genres)

    def sync(self):
        self.update_play_skip_rating_data()
        self.rename_file_to_pattern(self.path)
        self.model.update_from_dict(self.data)
        self.easyID3.update_from_dict(self.data)

    def save(self):
        self.sync()
        if self.easyID3.is_modified:
            LOGGER.info('Saving file changes...')
            self.easyID3.save()
        if session.is_modified(self.model):
            LOGGER.info('Committing model changes...')
            session.merge(self.model)
            session.commit()

    def match_meta_genre(self, genre):
        if not genre:
            return
        genre_mappings = [row.as_dict() for row in session.query(Genre).all()]
        prioritized_meta_genres = ['indie', 'electronic']

        cleaned_genre = clean_genre(genre)

        for prioritized_meta_genre in prioritized_meta_genres:
            for genre_mapping in [genre_mapping for genre_mapping in genre_mappings if genre_mapping['meta_genre'] ==
                    prioritized_meta_genre]:
                if clean_genre(genre_mapping['genre']) in cleaned_genre:
                    return genre_mapping['meta_genre'].title()

        for genre_mapping in [genre_mapping for genre_mapping in genre_mappings if genre_mapping['meta_genre'] not in
                prioritized_meta_genres]:
            if clean_genre(genre_mapping['genre']) in cleaned_genre:
                return genre_mapping['meta_genre'].title()

    # TODO: create function to handle deleted tracks

    def get_itunes_track_data(self, track_path, itunes_keys):
        # TODO: iTunes uses HTML encoding for some things (ampersands) and URL encoding for the rest
        with open('/Users/carmstrong/Music/iTunes/iTunes Music Library.xml', 'rb') as itunes_xml:
            tree = etree.parse(itunes_xml)

        itunes_track_path = 'file://' + urllib.quote(track_path.encode('utf-8'), safe="/(),'")
        location_node = tree.xpath('//string[text()="{}"]'.format(itunes_track_path))

        if not location_node:
            LOGGER.info('{} not found in iTunes XML file.'.format(itunes_track_path))
            return

        results = {}
        for itunes_key in itunes_keys:
            try:
                itunes_value = location_node[0].xpath("../key[text()='{}']".format(itunes_key))[0].getnext().text
                try:
                    itunes_value = int(itunes_value)
                except (ValueError, TypeError):
                    continue
                results.update({itunes_key: itunes_value})

            except IndexError:
                continue

        return results

    def update_play_skip_rating_data(self):

        itunes_mapping = {'Play Count': 'play_count',
                          'Skip Count': 'skip_count',
                          'Loved': 'loved'}

        itunes_results = self.get_itunes_track_data(self.path, itunes_mapping.keys())
        if itunes_results:
            for itunes_key, itunes_value in itunes_results.iteritems():
                self.__setattr__(itunes_mapping[itunes_key], itunes_value)

    def rename_file_to_pattern(self, file_path, directory_pattern='{album_artist}/{album}/', file_pattern='{artist} - {'
                                                                                                          'title}'):
        # TODO: account for when track data contains slashes in it (prob need to use os.join or whatever)
        current_filename = os.path.basename(file_path)
        file_extension = os.path.splitext(file_path)[1]

        mp3 = EasyID3Patched(file_path)

        artist = mp3.get('artist')[0] if 'artist' in mp3.keys() else ''
        album_artist = mp3.get('albumartist')[0] if 'albumartist' in mp3.keys() else ''
        title = mp3.get('title')[0] if 'title' in mp3.keys() else ''
        album = mp3.get('album')[0] if 'album' in mp3.keys() else ''

        # use artist/album_artist if the other is blank
        artist = artist or album_artist
        album_artist = album_artist or artist

        if all([artist, title]):
            new_filename = str(file_pattern + file_extension).format(artist=artist.strip(),
                                                                     title=title.strip())
            new_directory = str(TRACK_DIRECTORY + directory_pattern).format(artist=artist.strip(),
                                                                            album_artist=album_artist.strip(),
                                                                            title=title.strip(),
                                                                            album=album.strip())
            new_path = new_directory + new_filename
            self.path = re.sub(r'/{2,}', '/', new_path)
        else:
            self.path = TRACK_DIRECTORY + current_filename


def get_itunes_track_data(itunes_key):
    with open('/Users/carmstrong/Music/iTunes/iTunes Music Library.xml', 'rb') as itunes_xml:
        tree = etree.parse(itunes_xml)

    queried_tracks = tree.xpath("/plist/dict/dict/dict/key[text()='{}']".format(itunes_key))

    results = []

    for queried_track in queried_tracks:

        if itunes_key == 'Loved':
            key_value = True
        else:
            key_value = queried_track.getnext().text
        filename = queried_track.xpath("../key[text()='Location']")[0].getnext().text

        results.append({itunes_key: key_value,
                        "file_path": urllib.unquote(filename[7:])})

    return results


def update_db_for_itunes_data(itunes_data, db_field):
    db_tracks = session.query(SavedTrack).filter(SavedTrack.path.in_([i['file_path'] for i in itunes_data])).all()
    itunes_key = [key for key in itunes_data[0].keys() if key != 'file_path'][0]  # gross
    for db_track in db_tracks:
        db_track.__setattr__(db_field, [track[itunes_key] for track in itunes_data if track['file_path'] ==
                                        db_track.path][0])
        session.add(db_track)

    session.commit()


def update_play_skip_rating_data():
    skipped_tracks = get_itunes_track_data('Skip Count')
    update_db_for_itunes_data(skipped_tracks, 'skip_count')

    played_tracks = get_itunes_track_data('Play Count')
    update_db_for_itunes_data(played_tracks, 'play_count')

    loved_tracks = get_itunes_track_data('Loved')
    update_db_for_itunes_data(loved_tracks, 'loved')


def delete_empty_directories(root_directory=TRACK_DIRECTORY):
    audio_extensions = ['.mp3', '.flac', '.m4a', '.wma']
    for directory, subdirs, filenames in os.walk(root_directory, topdown=False):
        audio_files = [filename for filename in filenames for audio_extension in audio_extensions if filename.endswith(
            audio_extension)]
        if not audio_files and not subdirs:
            for file in filenames:
                os.remove(os.path.join(directory, file))
            os.rmdir(directory)


# def rename_library():
#     track_paths = get_track_paths(TRACK_DIRECTORY)
# 
#     for track_path in track_paths:
#         new_path = rename_file_to_pattern(track_path)
#         if not os.path.exists(os.path.dirname(new_path)):
#             os.makedirs(os.path.dirname(new_path))
#         os.rename(track_path, rename_file_to_pattern(track_path))
# 
#     delete_empty_directories()

def sync_library(enrich=True):
    track_paths = get_track_paths(TRACK_DIRECTORY)
    tracks = [Track(track_path) for track_path in track_paths]
    for track in tracks:
        if enrich:
            track.enrich()
        track.save()
