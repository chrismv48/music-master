"""Downloads provided songs from youtube"""
from difflib import SequenceMatcher

import requests

from models.models import session, QueuedTrack, convert_query_results


# search for youtube results using track artist + title
KEY = "AIzaSyAhfGE6RQxCr0q-p1_NhHYUrB0X4ixfIbs"
base_url = "https://www.googleapis.com/youtube/v3/search"
params = {"q": "query",
          "part": "snippet",
          "type": "video",
          "max_results": 3,
          "key": KEY
          }


def get_best_result(search_results, query):
    results = []
    for result in search_results['items']:
        result_dict = {"youtube_video_id": result['id']['videoId'],
                       "youtube_video_title": result['snippet']['title']}
        result_dict['similarity_score'] = SequenceMatcher(None, query, result_dict['youtube_video_title']).ratio()
        results.append(result_dict)

    return max(results, key=lambda x: x['similarity_score'])

def run():

    tracks_to_search_for = session.query(QueuedTrack).filter(QueuedTrack.youtube_video_id == None).all()
    #tracks_to_search_for = convert_query_results(tracks_to_search_for)
    tracks_to_search_for = [track.to_dict() for track in tracks_to_search_for]

    for track in tracks_to_search_for:
        query = track['artist'] + ' ' + track['title']
        params['q'] = query

        resp = requests.get(url=base_url, params=params, verify=False)
        json_response = resp.json()
        if json_response['items']:
            track.update(get_best_result(resp.json(), query))
            track.pop('similarity_score')
            session.merge(QueuedTrack(**track))
            session.commit()

    session.close()


if __name__ == '__main__':

    run()