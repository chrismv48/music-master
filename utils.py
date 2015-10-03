import hashlib
import os
from datetime import datetime
from mutagen.easyid3 import EasyID3
from difflib import SequenceMatcher
import re
import psutil
from EasyID3Patched import EasyID3Patched
from config import TRACK_DIRECTORY


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


def is_file_listener_running(module_name='file_listener.py'):
    for pid in psutil.pids():
        process = psutil.Process(pid)
        if process.name() == 'python' and module_name in ''.join(process.cmdline()):
            return True

    return False


def run_file_listener():
    if not is_file_listener_running():
        psutil.Popen(
            '/Users/carmstrong/Envs/music-master/bin/python /Users/carmstrong/Projects/music_master/file_listener.py',
            shell=True)


def set_id3_tag(id3_tag, value, library_directory=TRACK_DIRECTORY):
    track_paths = get_track_paths(library_directory)
    for track_path in track_paths:
        audio_file = EasyID3Patched(track_path)
        if audio_file.get(id3_tag):
            audio_file[id3_tag] = value
            audio_file.save()


def rename_file_to_pattern(file_path, directory_pattern='{album_artist}/{album}/', file_pattern='{artist} - {title}'):
    current_filename = os.path.basename(file_path)
    file_extension = os.path.splitext(file_path)[1]

    mp3 = EasyID3Patched(file_path)

    artist = mp3.get('artist')[0] if 'artist' in mp3.keys() else ''
    album_artist = mp3.get('albumartist')[0] if 'albumartist' in mp3.keys() else ''
    title = mp3.get('title')[0] if 'title' in mp3.keys() else ''
    album = mp3.get('album')[0] if 'album' in mp3.keys() else ''

    # use artist/album_artist if the other is blank
    artist = artist or album_artist
    album_artist = album_artist or artist

    if all([artist, title]):
        new_filename = str(file_pattern + file_extension).format(artist=artist.strip(),
                                                                 title=title.strip())
        new_directory = str(TRACK_DIRECTORY + directory_pattern).format(artist=artist.strip(),
                                                                        album_artist=album_artist.strip(),
                                                                        title=title.strip(),
                                                                        album=album.strip())
        new_path = new_directory + new_filename
        new_path = re.sub(r'/{2,}', '/', new_path)
    else:
        new_path = TRACK_DIRECTORY + current_filename

    return new_path


def rename_library():
    track_paths = get_track_paths(TRACK_DIRECTORY)

    for track_path in track_paths:
        new_path = rename_file_to_pattern(track_path)
        if not os.path.exists(os.path.dirname(new_path)):
            os.makedirs(os.path.dirname(new_path))
        os.rename(track_path, rename_file_to_pattern(track_path))

    delete_empty_directories()


def delete_empty_directories(root_directory=TRACK_DIRECTORY):
    for directory, subdirs, filenames in os.walk(root_directory, topdown=False):
        safe_filenames = [filename for filename in filenames if filename != '.DS_Store']
        if not safe_filenames and not subdirs:
            for file in filenames:
                os.remove(os.path.join(directory, file))
            os.rmdir(directory)
