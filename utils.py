import hashlib
import os
from datetime import datetime
from mutagen.easyid3 import EasyID3
from difflib import SequenceMatcher
import re


def get_track_paths(dir):
    """Returns a list of all filepaths in the given dir ending with the mp3 extension."""
    track_names = []
    for root, subdirs, filenames in os.walk(dir):
        for filename in filenames:
            if filename.endswith('.mp3'):
                track_names.append(os.path.join(root, filename))

    return track_names

def convert_floats(value):
    if isinstance(value, float):
        return int(value * 100)


def edit_id3_tags(track_path, **kwargs):
    """Edits and saves an mp3 file's ID3 tags"""
    track_mp3 = EasyID3(track_path)
    track_mp3.mp3.update(**kwargs)
    track_mp3.save()


def calculate_similarity(origin_term, matched_term, clean_terms=False):
    if clean_terms:
        origin_term = re.sub(r'\W+', '', origin_term).strip().lower()
        matched_term = re.sub(r'\W+', '', matched_term).strip().lower()
    return SequenceMatcher(None, origin_term, matched_term).ratio()


def track_modified_date(track_path):
    timestamp = os.path.getmtime(track_path)
    return datetime.fromtimestamp(timestamp)



def calculate_md5(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def clean_search_term(search_term):
    return re.sub(r'\W+', ' ', search_term).strip()