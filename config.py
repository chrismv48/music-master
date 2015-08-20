import os
import sys
import logging

logFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
LOGGER = logging.getLogger('music_master')

fileHandler = logging.FileHandler("music_master.log")
fileHandler.setFormatter(logFormatter)
LOGGER.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
LOGGER.addHandler(consoleHandler)
LOGGER.setLevel('DEBUG')

TRACK_DIRECTORY = '/Users/carmstrong/Projects/music_master/tracks/'
ECHONEST_API_KEY = "JLNEEHJ7URFXQQZIK"
ACOUST_ID_API_KEY = 'K0TgpFct'
MUSICBRAINZ_USERNAME = 'chrismv48'
MUSICBRAINZ_PASSWORD = 'Dockside6'
MUSICBRAINZ_USER_AGENT = ("Music Master", "0.1", "chris.r.armstrong@gmail.com")

YOUTUBE_API_KEY = "AIzaSyAhfGE6RQxCr0q-p1_NhHYUrB0X4ixfIbs"

_to_model = {'artist': 'artist',
             'title': 'title',
             'bpm': 'tempo',
             'discnumber': 'valence',
             'tracknumber': 'energy',
             'genre': 'genres',
             'acoustid_fingerprint': 'fingerprint',
             'length': 'duration',
             'albumartist': 'album_artist'}

mapping = {'to_model': _to_model,
           'to_file': {v: k for k, v in _to_model.iteritems()}}
