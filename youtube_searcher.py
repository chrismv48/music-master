"""Downloads provided songs from youtube"""
from difflib import SequenceMatcher

import requests
from config import YOUTUBE_API_KEY
from models.models import session, QueuedTrack


# search for youtube results using track artist + title
base_url = "https://www.googleapis.com/youtube/v3/search"
params = {"q": "query",
          "part": "snippet",
          "type": "video",
          "max_results": 3,
          "key": YOUTUBE_API_KEY
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
    tracks_to_search_for = [track.as_dict() for track in tracks_to_search_for]

    try:
        for track in tracks_to_search_for:
            query = track['artist'] + ' ' + track['title']
            params['q'] = query

            resp = requests.get(url=base_url, params=params, verify=False)
            json_response = resp.json()
            if json_response['items']:
                track.update(get_best_result(resp.json(), query))
                track.pop('similarity_score')
                session.merge(QueuedTrack(**track))
    except:
        raise

    finally:
        session.commit()


if __name__ == '__main__':
    run()
