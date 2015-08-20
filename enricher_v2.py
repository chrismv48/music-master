"""Docstring goes here"""
import time
import os
import re

from pyechonest import artist, song, config

from utils import calculate_similarity
from config import ECHONEST_API_KEY
from library_v2 import update_orm
from models.models import session, SavedTrack, QueuedTrack

config.ECHO_NEST_API_KEY = ECHONEST_API_KEY

# TODO: query musicbrainz with fingerprint to get artist/title/album info

def search_musicbrainz(fingerprint):
    pass

def clean_search_term(search_term):
    return re.sub(r'\W+', ' ', search_term).strip()


def search_echonest_artist_terms(artist_name):
    artist_results = artist.search(name=artist_name)
    if not artist_results:
        print "No artist found: {}".format(artist_name)
        return None
    if artist_results[0].name.lower() == artist_name.lower():
        artist_terms = artist_results[0].terms
        term_names = [term['name'] for term in artist_terms[:2]]

        return term_names
    else:
        print "Artist name did not match top result: {} vs {}".format(artist_name, artist_results[0].name)
        return None


def search_echonest_for_song(search_term, match_threshold=.75):
    cleaned_search_term = clean_search_term(search_term)
    search_results = song.search(combined=cleaned_search_term)
    if search_results:
        score_results = []
        for search_result in search_results:
            matched_term = search_result.artist_name + ' ' + search_result.title
            similarity_score = calculate_similarity(cleaned_search_term,
                                                    matched_term,
                                                    match_threshold)
            score_results.append({'similarity_score': similarity_score,
                                  'song_object': search_result})

        top_score_result = max(score_results, key=lambda x: x['similarity_score'])
        if top_score_result['similarity_score'] >= match_threshold:
            return top_score_result['song_object']
            # TODO: fix unicode errors (temp fix by deleting print stmts)
            # else:
            #     print u'''Similarity score of {similarity_score} below threshold of {match_threshold}\n
            #      Search Term: {cleaned_search_term}\n
            #      Matched Term: {matched_term}
            #      '''.format(match_threshold=match_threshold,
            #                 matched_term=top_score_result['song_object'].artist_name.encode('utf-8') + ' ' +
            #                              top_score_result[
            #                                  'song_object'].title.encode('utf-8'),
            #                 cleaned_search_term=cleaned_search_term.encode('utf-8'),
            #                 similarity_score=top_score_result['similarity_score'])
    else:
        return None


def generate_artist_title_from_model(track_model):
    if all([track_model.artist,track_model.title]):
        return track_model.artist + ' ' + track_model.title
    else:
        return os.path.splitext(track_model.filename)[0]


def enrich_track(track_model):
    # TODO: submit to be analyzed if not found
    echonest_queried = False
    model_updated = False
    print 'Track {}'.format(track_model.artist + ' - ' + track_model.title if track_model.artist else
                            track_model.path)
    if not track_model.danceability:
        search_term_for_track = generate_artist_title_from_model(track_model)
        print 'Searching echonest for track using: {}'.format(search_term_for_track)
        top_score_result = search_echonest_for_song(search_term_for_track)
        echonest_queried = True
        if top_score_result:
            print 'Song found on Echonest: {} - {}'.format(top_score_result.artist_name,
                                                           top_score_result.title)
            audio_summary = top_score_result.get_audio_summary()
            track_artist = top_score_result.artist_name.encode('utf-8')
            track_title = top_score_result.title.encode('utf-8')
            audio_summary['artist'] = track_artist
            audio_summary['title'] = track_title
            track_model = update_orm(audio_summary, track_model)
            model_updated = True

    if not track_model.genres and track_model.artist:
        print 'Searching echonest for genres using artist {}' .format(track_model.artist)
        genres = search_echonest_artist_terms(track_model.artist)
        echonest_queried = True
        if genres:
            track_model.genres = genres[0]
            print 'Genre found: {}' .format(genres[0])
            model_updated = True

    if model_updated:
        session.merge(track_model)
        session.commit()
    else:
        print 'Track not updated'

    if echonest_queried:  # so the calling code can implement rate limiting if needed
        return True
    else:
        return False


def enrich_library():
    # use danceability as a proxy for whether the track has been enriched yet or not
    library_models = session.query(SavedTrack).filter(SavedTrack.danceability == None).all()
    queued_tracks_models = session.query(QueuedTrack).filter(QueuedTrack.danceability == None).all()

    all_models = library_models + queued_tracks_models

    for model in all_models:
        if enrich_track(model):
            time.sleep(2)
