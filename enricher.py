"""Docstring goes here"""
from datetime import timedelta, datetime

from pyechonest import song, artist, config
import time

from config import ECHONEST_API_KEY, LOGGER
from models.models import session
from utils import calculate_similarity

config.ECHO_NEST_API_KEY = ECHONEST_API_KEY

# TODO: this might be overwriting valid id3 data?

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
        term_names = [term['name'] for term in artist_terms[:2]]

        return term_names
    else:
        LOGGER.info("Artist name did not match top result: {} vs {}".format(artist_name, artist_results[0].name))
        return None


def enrich_track(track_model):
    # TODO: submit to be analyzed if not found
    if track_model.last_searched_echonest and track_model.last_searched_echonest > (
                track_model.last_searched_echonest - timedelta(days=7)):
        LOGGER.info('Track already enriched, skipping enrichment process.')
        return track_model
    LOGGER.info('Searching Echonest for track using: {}'.format(track_model.search_phrase))
    top_score_result = search_echonest_for_song(track_model.search_phrase)
    if top_score_result:
        LOGGER.info('Song found on Echonest: {} - {}'.format(top_score_result.artist_name,
                                                       top_score_result.title))
        audio_summary = top_score_result.get_audio_summary()
        track_artist = top_score_result.artist_name.encode('utf-8')
        track_title = top_score_result.title.encode('utf-8')
        audio_summary['artist'] = track_artist
        audio_summary['title'] = track_title
        audio_summary = {k: v*100 if v < 1 else v for k, v in audio_summary.iteritems()} # SQLAlchemy converts
        # values less than 1 to 0 before the validators can act.
        track_model.from_dict(audio_summary)
        time.sleep(2)
    else:
        LOGGER.info('Track not found in Echonest')

    if not track_model.genres and track_model.album_artist:
        LOGGER.info('Searching Echonest for genres using artist {}' .format(track_model.album_artist or
                                                                            track_model.artist))
        genres = search_echonest_artist_terms(track_model.album_artist)
        if genres:
            track_model.genres = genres[0]
            LOGGER.info('Genre found: {}' .format(genres[0]))

        time.sleep(2)

    track_model.last_searched_echonest = datetime.now()

    return track_model

