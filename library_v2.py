"""New library to accomodate for event driven syncing"""
from collections import namedtuple
import sys

from EasyID3Patched import EasyID3Patched

from acoustid import fingerprint_file

from config import TRACK_DIRECTORY
from models.models import SavedTrack, session
from utils import get_track_paths

reload(sys)
sys.setdefaultencoding("utf-8")



def load_track_tuple(file_path, clear_existing_tags=False):
    # TODO: may need to add logic for if track is being loaded for the first time, ie clear discnumber/tracknumber
    track_easyid3 = EasyID3Patched(file_path)
    if clear_existing_tags:
        track_easyid3.clear()
    if not track_easyid3.get('musicip_fingerprint'):
        track_easyid3['musicip_fingerprint'] = fingerprint_file(file_path, 30)[1]
        track_easyid3.save()
    track_fingerprint = track_easyid3['musicip_fingerprint'][0]
    Track = namedtuple('Track', ['easyID3', 'model', 'file_path', 'fingerprint'])
    track_model = session.query(SavedTrack).filter(SavedTrack.fingerprint == track_fingerprint).first()
    session.close()
    return Track(easyID3=track_easyid3, model=track_model, file_path=file_path,
                 fingerprint=track_fingerprint)


def load_library_tuples(library_directory=TRACK_DIRECTORY, clear_existing_tags=False):
    # TODO: this is slow as fuck
    track_paths = get_track_paths(library_directory)

    return [load_track_tuple(track_path, clear_existing_tags) for track_path in track_paths]

def force_sync(library_directory=TRACK_DIRECTORY, clear_existing_tags=False):
    track_paths = get_track_paths(library_directory)
    for track_path in track_paths:
        easyID3_track = EasyID3Patched(track_path)
        if clear_existing_tags:
            easyID3_track.clear()
        easyID3_track.save()


def apply_mapping(key, mapping):
    if key in mapping.keys():
        return mapping[key]
    else:
        return key


def translate_file_value(value):
    # convert list values to actual value cuz Mutagen is special
    # TODO all of this could be moved into model validation functions
    if isinstance(value, list):
        value = value[0]

    if isinstance(value, unicode) or isinstance(value, str):
        try:
            value = float(value)
            if value <= 1:
                return int(value * 100)
            else:
                return int(value)
        except ValueError:
            return value

    else:
        return value


def translate_model_value(value):
    # convert None/Null values to empty strings so Mutagen won't complain
    if not value:
        return u''

    # I assume decimals need to be whole percents here (energy/valuealence), then unicode it cuz Mutagen
    elif isinstance(value, float):
        if value <= 1:
            return unicode(int(value * 100))
        else:
            return unicode(int(value))

    # yup, Mutagen needs everything to be unicode/strings
    else:
        return unicode(value)


# def get_valid_keys(direction):
#     if direction == 'to_file':
#         return EasyID3.valid_keys.keys()
#     elif direction == 'to_model':
#         return SavedTrack.__dict__.keys()
#
#
# def update_orm(input_dict, orm):
#     """
#     Uses a dictionary (which could be the __dict__ attribute of another model) to create/modify another model
#     :param input_dict:
#     :param orm:
#     :return:
#     """
#     valid_orm_fields = [key for key in orm.__table__.columns.keys() if not key.startswith('_')]
#     for k, v in input_dict.iteritems():
#         if k in valid_orm_fields:
#             orm.__setattr__(k, v)
#
#     return orm
#
#
# def update_easyID3(input_dict, easyID3):
#     valid_easyid3_fields = EasyID3Patched.valid_keys.keys()
#     for k, v in input_dict.iteritems():
#         if k in valid_easyid3_fields:
#             easyID3[k] = v
#
#     return easyID3


# def update_model_with_easyid3(easyID3, model, file_path, fingerprint):
#     if not model:
#         model = SavedTrack()
#
#     translated_dict = translate_easyid3_to_model(easyID3, model)
#     translated_dict['path'] = file_path
#     translated_dict['fingerprint'] = fingerprint
#
#     model = update_orm(translated_dict, model)
#     session.merge(model)  # merge will not trigger db change if there is no update to apply
#     session.commit()
#     session.close()
#
#
# def update_easyID3_with_model(easyID3, model):
#     track_file_unmodified = {k: v for k, v in easyID3.iteritems()}
#     translated_dict = translate_model_to_easyid3(easyID3, model)
#     easyID3 = update_easyID3(translated_dict, easyID3)
#
#     if track_file_unmodified != {k: v for k, v in easyID3.iteritems()}:
#         easyID3.save()


# def translate_model_to_easyid3(easyID3, model):
#     return {apply_mapping(k, mapping['to_file']): translate_model_value(v) for k, v in model.__dict__.iteritems()}
#
#
# def translate_easyid3_to_model(easyID3, model):
#     return {apply_mapping(k, mapping['to_model']): translate_file_value(v) for k, v in easyID3.iteritems()}
