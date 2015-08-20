import os
import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

TRACK_DIRECTORY = '/Users/carmstrong/Projects/music_master/tracks/'
ECHONEST_API_KEY = "JLNEEHJ7URFXQQZIK"
ACOUST_ID_API_KEY = 'K0TgpFct'
MUSICBRAINZ_USERNAME = 'chrismv48'
MUSICBRAINZ_PASSWORD = 'Dockside6'
MUSICBRAINZ_USER_AGENT = ("Music Master", "0.1",  "chris.r.armstrong@gmail.com")

_to_model = {'artist': 'artist',
             'title': 'title',
             'bpm': 'tempo',
             'discnumber': 'valence',
             'tracknumber': 'energy',
             'genre': 'genres',
             'acoustid_fingerprint': 'fingerprint',
             'length': 'duration'}

mapping = {'to_model': _to_model,
           'to_file': {v: k for k, v in _to_model.iteritems()}}
