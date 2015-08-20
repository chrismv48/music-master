"""Docstring goes here"""

import acoustid
from config import TRACK_DIRECTORY
from utils import get_track_filenames

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

API_KEY = 'K0TgpFct'

track_filenames = get_track_filenames(TRACK_DIRECTORY)

for track_filename in track_filenames[10:]:
    print track_filename
    try:
        print next(acoustid.match(API_KEY, TRACK_DIRECTORY + track_filename))
    except StopIteration:
        print '*** No match found ***'

