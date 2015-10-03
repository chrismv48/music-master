"""Docstring goes here"""
from datetime import timedelta, datetime
import os
import re
import time

import acoustid

from EasyID3Patched import EasyID3Patched
from config import LOGGER, TRACK_DIRECTORY
from enricher import enrich_track, acoustid_lookup
from models.models import SavedTrack, session, Genre
from utils import get_track_paths


def load_track_with_fingerprint(track_path):
    LOGGER.info('Loading track...')
    easyID3_track = EasyID3Patched(track_path)
    if not all([easyID3_track.get('acoustid_fingerprint'), easyID3_track.get('length')]):
        LOGGER.info('No fingerprint; generating from AcoustID')
        duration, fingerprint = acoustid.fingerprint_file(track_path, 30)
        easyID3_track['length'], easyID3_track['acoustid_fingerprint'] = unicode(duration), unicode(fingerprint)
    return easyID3_track


def sync_library(library_directory=TRACK_DIRECTORY):
    track_paths = get_track_paths(library_directory)
    for track_path in track_paths:
        sync_file(track_path)


def sync_file(track_path, event_type='modified'):
    if event_type == 'created':
        time.sleep(2)  # we do this to let the downloader finish syncing the databases
        # file_create_trigger(easyID3_track)

    easyID3_track = load_track_with_fingerprint(track_path)
    saved_track = session.query(SavedTrack).filter(SavedTrack.fingerprint == easyID3_track['acoustid_fingerprint'][
        0]).first()

    if not saved_track:
        LOGGER.info('Track not found in database; creating...')
        saved_track = SavedTrack()

    else:
        LOGGER.info('Track found in database: {}'.format(saved_track))
        easyID3_track.update_from_dict(saved_track.as_dict())

    if not saved_track.last_searched_acoustid or saved_track.last_searched_acoustid < (
                saved_track.last_searched_acoustid - timedelta(days=7)):
        LOGGER.info('Doing AcoustID lookup for track artist, title and album...')
        acoustid_data = acoustid_lookup(easyID3_track.model_dict['fingerprint'],
                                        int(easyID3_track.model_dict['duration']))
        easyID3_track.update_from_dict(acoustid_data)
        saved_track.last_searched_acoustid = datetime.now()


    saved_track.from_dict(easyID3_track.model_dict)
    saved_track = enrich_track(saved_track)
    saved_track.meta_genre = match_meta_genre(saved_track.genres)
    easyID3_track.update_from_dict(saved_track.as_dict())

    if session.is_modified(saved_track):
        session.merge(saved_track)
        session.commit()

    if easyID3_track.is_modified:
        easyID3_track.save()



def rename_file_to_pattern(file_path, directory_pattern='{album_artist}/{album}/', file_pattern='{artist} - {title}'):
    # TODO: account for when track data contains slashes in it (prob need to use os.join or whatever
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
        new_path = re.sub(r'/{2,}', '/', new_path)
    else:
        new_path = TRACK_DIRECTORY + current_filename

    return new_path


def rename_library():
    track_paths = get_track_paths(TRACK_DIRECTORY)

    for track_path in track_paths:
        new_path = rename_file_to_pattern(track_path)
        if not os.path.exists(os.path.dirname(new_path)):
            os.makedirs(os.path.dirname(new_path))
        os.rename(track_path, rename_file_to_pattern(track_path))

    delete_empty_directories()


def delete_empty_directories(root_directory=TRACK_DIRECTORY):
    audio_extensions = ['.mp3', '.flac', '.m4a', '.wma']
    for directory, subdirs, filenames in os.walk(root_directory, topdown=False):
        audio_files = [filename for filename in filenames for audio_extension in audio_extensions if filename.endswith(
            audio_extension)]
        if not audio_files and not subdirs:
            for file in filenames:
                os.remove(os.path.join(directory, file))
            os.rmdir(directory)


def clean_genre(genre):
    return re.sub('[\W_]+', ' ', genre).lower()


def match_meta_genre(genre):
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


sync_library()