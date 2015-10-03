import os
import sys
import logging
import json

logFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
LOGGER = logging.getLogger('music_master')
LOG_DIRECTORY = os.getcwd()
fileHandler = logging.FileHandler(LOG_DIRECTORY + "/music_master.log")
fileHandler.setFormatter(logFormatter)
LOGGER.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
LOGGER.addHandler(consoleHandler)
LOGGER.setLevel('DEBUG')

with open('config.json') as login_data:
    login_data = json.load(login_data)

TRACK_DIRECTORY = '/Users/carmstrong/Google Drive/Music/'
ECHONEST_API_KEY = login_data['echonest_api_key']
ACOUST_ID_API_KEY = login_data['acoust_id_api_key']
MUSICBRAINZ_USERNAME = login_data['musicbrainz_username']
MUSICBRAINZ_PASSWORD = login_data['musicbrainz_password']
MUSICBRAINZ_USER_AGENT = ("Music Master", "0.1", login_data['email'])

YOUTUBE_API_KEY = login_data['youtube_api_key']

_to_file_mapping = {'artist': 'artist',
                    'title': 'title',
                    'tempo': 'bpm',
                    'valence': 'discnumber',
                    'energy': 'tracknumber',
                    'genres': 'genre',
                    'fingerprint': 'acoustid_fingerprint',
                    'duration': 'length',
                    'album_artist': 'albumartist',
                    'source': 'composer',
                    'meta_genre': 'grouping'}

mapping = {'to_file': _to_file_mapping,
           'to_model': {v: k for k, v in _to_file_mapping.iteritems() if k not in ['valence', 'energy']}}
