import os
import sys
import logging

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

TRACK_DIRECTORY = '/Users/carmstrong/Google Drive/Music/'
ECHONEST_API_KEY = "JLNEEHJ7URFXQQZIK"
ACOUST_ID_API_KEY = 'K0TgpFct'
MUSICBRAINZ_USERNAME = 'chrismv48'
MUSICBRAINZ_PASSWORD = 'Dockside6'
MUSICBRAINZ_USER_AGENT = ("Music Master", "0.1", "chris.r.armstrong@gmail.com")

YOUTUBE_API_KEY = "AIzaSyAhfGE6RQxCr0q-p1_NhHYUrB0X4ixfIbs"

_to_file_mapping = {'artist': 'artist',
                    'title': 'title',
                    'tempo': 'bpm',
                    'valence': 'discnumber',
                    'energy': 'tracknumber',
                    'genres': 'genre',
                    'fingerprint': 'acoustid_fingerprint',
                    'duration': 'length',
                    'album_artist': 'albumartist'}

mapping = {'to_file': _to_file_mapping,
           'to_model': {v: k for k, v in _to_file_mapping.iteritems() if k not in ['valence', 'energy']}}
