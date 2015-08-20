"""Interface to library"""
from collections import namedtuple
from datetime import datetime
import os

from mutagen.easyid3 import EasyID3
from acoustid import fingerprint_file

from config import TRACK_DIRECTORY
from models.models import session, SavedTrack
from utils import get_track_paths, track_modified_date


def load_track(file_path):

    track_fingerprint = fingerprint_file(file_path)

    Track = namedtuple('Track', ['file_info', 'model'])
    track_easyid3 = EasyID3(file_path)
    track_model = session.query(SavedTrack).filter(SavedTrack.fingerprint == track_fingerprint).first()

    return Track(file_info=track_easyid3, model=track_model)


def load_tracks(library_directory=TRACK_DIRECTORY):
    #TODO: Tracks should be paired based on MD5 hash or similar instead of the filename
    Track = namedtuple('Track', ['file_info', 'model'])

    tracks = []

    db_tracks = session.query(SavedTrack).all()
    db_track_filenames = [db_track.filename for db_track in db_tracks]
    track_filenames = get_track_paths(library_directory)  # TODO make this recursive

    for track_filename in track_filenames:

        if track_filename in db_track_filenames:
            db_track_index = db_track_filenames.index(track_filename)
            track_file = EasyID3(library_directory + track_filename)
            track = Track(file_info=track_file,
                          model=db_tracks[db_track_index])
            tracks.append(track)
            db_tracks.pop(db_track_index)
            db_track_filenames.pop(db_track_index)
        else:
            track_file = EasyID3(library_directory + track_filename)
            if track_file.get('discnumber'):
                track_file['discnumber'] = []
            if track_file.get('discnumber'):
                track_file['tracknumber'] = []
            track = Track(file_info=track_file,
                          model=None)
            tracks.append(track)

    for remaining_db_track in db_tracks:
        track = Track(model=remaining_db_track, file_info=None)
        tracks.append(track)

    return tracks


def create_or_modify_orm(input_dict, orm):
    """
    Uses a dictionary (which could be the __dict__ attribute of another model) to create/modify another model
    :param input_dict:
    :param orm:
    :return:
    """
    valid_orm_fields = [key for key in orm.__table__.columns.keys() if not key.startswith('_')]
    for k, v in input_dict.iteritems():
        if k in valid_orm_fields:
            orm.__setattr__(k, v)

    return orm

mapping = {'to_model': {'artist': 'artist',
                        'title': 'title',
                        'bpm': 'tempo',
                        'discnumber': 'valence',
                        'tracknumber': 'energy',
                        'genre': 'genres'},
           'to_file': {'artist': 'artist',
                       'title': 'title',
                       'tempo': 'bpm',
                       'valence': 'discnumber',
                       'energy': 'tracknumber',
                       'genres': 'genre'}}


def get_valid_keys(direction):
    if direction == 'to_file':
        return EasyID3.valid_keys.keys()
    elif direction == 'to_model':
        return SavedTrack.__dict__.keys()

def apply_mapping(key, mapping):
    if key in mapping.keys():
        return mapping[key]
    else:
        return key

def translate_data(input_dict, direction='to_file', mapping=mapping):
    valid_keys = get_valid_keys(direction)

    # apply mapping
    translated_dict = {apply_mapping(k, mapping[direction]): v for k, v in input_dict.iteritems()}

    # drop invalid items based on new fields
    translated_dict = {k:v for k, v in translated_dict.iteritems() if k in valid_keys}
    if not translated_dict:
        return {}

    for k, v in translated_dict.iteritems():
        if direction == 'to_file':
            # convert None/Null values to empty strings so Mutagen won't complain
            if not v:
                v = u''

            # I assume decimals need to be whole percents here (energy/valence), then unicode it cuz Mutagen
            elif isinstance(v, float):
                if v <= 1:
                    v = unicode(int(v * 100))
                else:
                    v = unicode(int(v))

            # yup, Mutagen needs everything to be unicode/strings
            else:
                v = unicode(v)

        elif direction == 'to_model':
            # convert list values to actual value cuz Mutagen is special
            if isinstance(v, list):
                v = v[0]

            if isinstance(v, unicode):
                try:
                    v = int(v)
                except ValueError:
                    pass

            elif isinstance(v, float):
                if v <= 1:
                    v = unicode(int(v * 100))
                else:
                    v = unicode(int(v))


        translated_dict[k] = v

    return translated_dict


def update_track_model(track_model, update_dict):
    for k, v in update_dict.iteritems():
        track_model.__setattr__(k, v)

    return track_model


def merge_track_model_and_file(track_file, track_model=None, track_data=None, mapping=mapping):
    """
    Synchronizes track meta data between the file and track model. If no model is provided, we create one.

    :param track_file: Mutagen EasyID3 object
    :param track_model: SQLAlchemy query result object
    :param track_data: Optionally include dictionary to update track_file and track_model with
    :param mapping: A mapping to translate field names between id3 tags and db fields
    """

    # TODO: add logging
    # TODO: convert audio_summary decimals to integers
    if track_file is None:  # we must check specifically for None type because an EasyID3 object with no attributes
    # evaluates to False
        return

    track_file_unmodified = {k:v for k, v in track_file.iteritems()}
    track_data = {} if not track_data else track_data
    track_data.update({'filename':os.path.basename(track_file.filename)})

    if not track_model:
        track_model = SavedTrack()
        track_model_last_modified_date = datetime(1970, 1, 1)
        track_model_unmodified = None
    else:
        track_model_last_modified_date = track_model.last_modified
        track_model_unmodified = track_model.__dict__.copy()

    track_file_last_modified_date = track_modified_date(track_file.filename)
    track_data['filename'] = os.path.split(track_file.filename)[-1]

    if not track_model or track_file_last_modified_date > track_model_last_modified_date:
        track_model = update_track_model(track_model, translate_data(track_data, 'to_model'))
        track_file.update(translate_data(track_data, 'to_file'))
        track_data.update(track_file)
        track_model = update_track_model(track_model, translate_data(track_data, 'to_model'))

    else:
        track_file.update(translate_data(track_data, 'to_file'))
        track_model = update_track_model(track_model, translate_data(track_data, 'to_model'))
        track_data.update(track_model.__dict__)
        track_file.update(translate_data(track_data, 'to_file'))

    if track_file_unmodified != track_file:
        track_file.save()
    if track_model_unmodified != track_model.__dict__:
        session.merge(track_model)
        session.commit()


library = load_tracks()

# mp3_file = EasyID3(TRACK_DIRECTORY + 'AYER - In My Headphones (TKDJS Remix).mp3')
# track_model = session.query(SavedTrack).all()[1]
# merge_track_model_and_file(mp3_file, track_model, track_data={'genre': 'rock n roll', 'energy': 67})
