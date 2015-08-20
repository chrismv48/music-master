"""Loads all tracks and fills in missing ID3 attributes where possible and then merges into db"""

import hashlib
from utils import calculate_similarity, convert_floats
from config import ECHONEST_API_KEY
from pyechonest import track, artist, song, config
import os
import re
import time
from library import library, merge_track_model_and_file


def get_artist_terms(artist_name):
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
    cleaned_search_term = re.sub(r'\W+', ' ', search_term).strip()
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

def run():

    config.ECHO_NEST_API_KEY = ECHONEST_API_KEY
    tracks_with_files = [track for track in library if track.file_info is not None]
    # First, synchronize tracks
    for track in tracks_with_files:
        track.file_info.clear()
        merge_track_model_and_file(track_file=track.file_info,
                                   track_model=track.model)

    for track in tracks_with_files:
        print track
        # track.file_info.clear()
        echonest_queried = False
        audio_summary = None
        track_data = {}
        track_artist = track.file_info.get('artist')[0] if track.file_info.get('artist') else None
        track_title = track.file_info.get('title')[0] if track.file_info.get('title') else None
        track_filename = os.path.basename(track.file_info.filename)
        if not all([track_artist, track_title, track.file_info.get('bpm'), track.file_info.get('discnumber'),
                    track.file_info.get('tracknumber')]):
            print 'Track missing info, searching Echonest'
            top_score_result = search_echonest_for_song(track_filename[:-4])
            if top_score_result:
                print 'Song found in Echonest...'
                audio_summary = top_score_result.get_audio_summary()
                track_data.update(audio_summary)
                track_artist = top_score_result.artist_name.encode('utf-8')
                track_title = top_score_result.title.encode('utf-8')
                track_data['artist'] = track_artist
                track_data['title'] = track_title
                echonest_queried = True

        if 'genre' not in track.file_info.keys() and track_artist:
            genres = get_artist_terms(track_artist)
            if genres:
                print 'Genre(s) found: {}'.format(genres)
                track_data['genre'] = genres[0]
            echonest_queried = True
        if track_data:
            merge_track_model_and_file(track_file=track.file_info,
                                       track_model=track.model,
                                       track_data=track_data
                                       )

        print '=========================================='
        print '\n'

        if echonest_queried:
            time.sleep(4)
        else:
            continue

if __name__ == '__main__':
    run()