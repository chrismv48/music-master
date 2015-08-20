"""Docstring goes here"""
import acoustid

from EasyID3Patched import EasyID3Patched
from config import ACOUST_ID_API_KEY
from models.models import SavedTrack, session


def load_track_with_fingerprint(track_path):
    easyID3_track = EasyID3Patched(track_path)
    if not all([easyID3_track.get('acoustid_fingerprint'), easyID3_track.get('length')]):
        duration, fingerprint = acoustid.fingerprint_file(track_path, 30)
        easyID3_track['length'], easyID3_track['acoustid_fingerprint'] = unicode(duration), unicode(fingerprint)
    return easyID3_track


def file_change_trigger(track_path):
    # load into mutagen
    # determine if fingerprint exists, if not create it
    easyID3_track = load_track_with_fingerprint(track_path)
    # determine if needs musicbrainz data (id?)
    if not easyID3_track.get('musicbrainz_releasetrackid'):
        acoustid_data = acoustid_lookup(easyID3_track.model_dict['fingerprint'],
                                        int(easyID3_track.model_dict['duration']))
        easyID3_track.update_from_dict(acoustid_data)

    saved_track = session.query(SavedTrack).filter(SavedTrack.fingerprint == easyID3_track.model_dict[
        'fingerprint']).first()
    if not saved_track:
        saved_track = SavedTrack()
    saved_track.from_dict(easyID3_track.model_dict)
    if session.is_modified(saved_track):
        session.merge(saved_track)
        session.commit()
    if easyID3_track.is_modified:
        easyID3_track.save()

        # update/create model


def acoustid_lookup(fingerprint, duration):
    results = acoustid.lookup(ACOUST_ID_API_KEY, fingerprint, duration, meta='recordings + releasegroups')
    if results['results'] and results['results'][0].get('recordings'):
        recording = results['results'][0]['recordings'][0]
        recording_id = recording['id']
        recording_artists = recording['artists']
        recording_title = recording['title']
        album_artist = recording_artists[0]['name']
        artist = ''.join([artist['name'] + artist.get('joinphrase', '') for artist in recording_artists])
        album = recording['releasegroups'][0]['title']

        return {'musicbrainz_releasetrackid': recording_id,
                'title': recording_title,
                'albumartist': album_artist,
                'artist': artist,
                'album': album}

    else:
        return {}