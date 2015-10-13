"""Docstring goes here"""
from datetime import timedelta, datetime
import time

import acoustid
from pyechonest import song, artist, config

from config import ECHONEST_API_KEY, LOGGER, ACOUST_ID_API_KEY
from utils import calculate_similarity

config.ECHO_NEST_API_KEY = ECHONEST_API_KEY


def search_echonest_for_song(search_term, match_threshold=.75):
    search_results = song.search(combined=search_term)
    if search_results:
        score_results = []
        for search_result in search_results:
            matched_term = search_result.artist_name + ' ' + search_result.title
            similarity_score = calculate_similarity(search_term,
                                                    matched_term,
                                                    match_threshold)
            score_results.append({'similarity_score': similarity_score,
                                  'song_object': search_result})

        top_score_result = max(score_results, key=lambda x: x['similarity_score'])
        if top_score_result['similarity_score'] >= match_threshold:
            return top_score_result['song_object']


def search_echonest_artist_terms(artist_name):
    artist_results = artist.search(name=artist_name)
    if not artist_results:
        LOGGER.info('Artist not found in Echonest')
        return None
    if artist_results[0].name.lower() == artist_name.lower():
        artist_terms = artist_results[0].terms
        if artist_terms:
            return max(artist_terms, key=lambda x: x['weight'] * x['frequency'])['name']
        else:
            return None
    else:
        LOGGER.info("Artist name did not match top result: {} vs {}".format(artist_name, artist_results[0].name))
        return None


def enrich_track(track_data):
    # TODO: submit to be analyzed if not found
    if track_data.last_searched_echonest and track_data.last_searched_echonest > (
                track_data.last_searched_echonest - timedelta(days=7)):
        LOGGER.info('Track already enriched, skipping enrichment process.')
        return track_data

    LOGGER.info('Searching Echonest for track using: {}'.format(track_data.search_phrase))
    top_score_result = search_echonest_for_song(track_data.search_phrase)
    if top_score_result:
        LOGGER.info('Song found on Echonest: {} - {}'.format(top_score_result.artist_name,
                                                             top_score_result.title))
        audio_summary = top_score_result.get_audio_summary()
        track_artist = top_score_result.artist_name.encode('utf-8')
        track_title = top_score_result.title.encode('utf-8')
        audio_summary['artist'] = track_artist
        audio_summary['title'] = track_title
        audio_summary = {k: v * 100 if v and v < 1 else v for k, v in audio_summary.iteritems()}  # SQLAlchemy converts
        # values less than 1 to 0 before the validators can act.
        track_data.from_dict(audio_summary)
        time.sleep(2)
    else:
        LOGGER.info('Track not found in Echonest')
    if not track_data.genres and (track_data.album_artist or track_data.artist):
        LOGGER.info('Searching Echonest for genres using artist {}'.format(track_data.album_artist or
                                                                           track_data.artist))
        top_term = search_echonest_artist_terms(track_data.album_artist or track_data.artist)
        if top_term:
            track_data.genres = top_term.title()
            LOGGER.info('Genre found: {}'.format(top_term))

        time.sleep(2)

    track_data.last_searched_echonest = datetime.now()

    return track_data


def acoustid_lookup(fingerprint, duration):
    results = acoustid.lookup(ACOUST_ID_API_KEY, fingerprint, duration, meta='recordings + releasegroups')
    if results.get('results') and results['results'][0].get('recordings'):
        LOGGER.info('AcoustID result found!')
        recordings = results['results'][0]['recordings']
        recording = max(recordings, key=lambda x: len(x.keys()))
        recording_id = recording['id']
        recording_artists = recording['artists']
        recording_title = recording['title']
        album_artist = recording_artists[0]['name']
        artist = ''.join([artist['name'] + artist.get('joinphrase', '') for artist in recording_artists])
        album = recording['releasegroups'][0]['title']  # TODO: the results of this are often inconsistent

        return {'musicbrainz_releasetrackid': recording_id,
                'title': recording_title,
                'artist': artist,
                'albumartist': album_artist,
                'album': album}

    else:
        LOGGER.info('No AcoustID results found.')
        return {}


