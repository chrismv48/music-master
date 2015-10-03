"""Docstring goes here"""
import acoustid
from datetime import timedelta, datetime
import time

from EasyID3Patched import EasyID3Patched
from config import ACOUST_ID_API_KEY, LOGGER, TRACK_DIRECTORY
from enricher import enrich_track
from models.models import SavedTrack, session, QueuedTrack
from utils import get_track_paths


def load_track_with_fingerprint(track_path):
    LOGGER.info('Loading track...')
    easyID3_track = EasyID3Patched(track_path)
    if not all([easyID3_track.get('acoustid_fingerprint'), easyID3_track.get('length')]):
        LOGGER.info('No fingerprint; generating from AcoustID')
        duration, fingerprint = acoustid.fingerprint_file(track_path, 30)
        easyID3_track['length'], easyID3_track['acoustid_fingerprint'] = unicode(duration), unicode(fingerprint)
    return easyID3_track

def force_sync(library_directory=TRACK_DIRECTORY):
    track_paths = get_track_paths(library_directory)
    for track_path in track_paths:
        sync_file(track_path)


# def file_create_trigger(easyID3_track):
#     queued_track = session.query(QueuedTrack).filter(QueuedTrack.fingerprint == easyID3_track.model_dict[
#     'fingerprint']).first()
#     if queued_track:
#         saved_track = SavedTrack()
#         saved_track.from_dict(queued_track.as_dict)
#         saved_track.path = easyID3_track.filename
#         saved_track.fingerprint = easyID3_track.model_dict['fingerprint']
#         session.add(saved_track)
#         session.delete(queued_track)
#         session.commit()
#         LOGGER.info('Sucessfully transferred queued track data for new track')
#     else:
#         LOGGER.info('No queued track data found')
#         return

def sync_file(track_path, event_type='modified'):

    if event_type == 'created':
        time.sleep(2)   # we do this to let the downloader finish syncing the databases
        #file_create_trigger(easyID3_track)

    saved_track = session.query(SavedTrack).filter(SavedTrack.path == track_path).first()
    if not saved_track:
        LOGGER.info('Track not found in database; creating...')
        saved_track = SavedTrack()
        easyID3_track = load_track_with_fingerprint(track_path)

    else:
        LOGGER.info('Track found in database:')
        LOGGER.info(saved_track)
        easyID3_track = EasyID3Patched(track_path)
        easyID3_track.update_from_dict(saved_track.as_dict())

    if not saved_track.last_searched_acoustid or saved_track.last_searched_acoustid < (
            saved_track.last_searched_acoustid - timedelta(days=7)):
        LOGGER.info('Doing AcoustID lookup for track data...')
        acoustid_data = acoustid_lookup(easyID3_track.model_dict['fingerprint'],
                                        int(easyID3_track.model_dict['duration']))
        easyID3_track.update_from_dict(acoustid_data)
        saved_track.last_searched_acoustid = datetime.now()

    saved_track.from_dict(easyID3_track.model_dict)
    saved_track = enrich_track(saved_track)
    easyID3_track.update_from_dict(saved_track.as_dict())

    if session.is_modified(saved_track):
        session.merge(saved_track)
        session.commit()

    if easyID3_track.is_modified:
        easyID3_track.save()


def acoustid_lookup(fingerprint, duration):
    results = acoustid.lookup(ACOUST_ID_API_KEY, fingerprint, duration, meta='recordings + releasegroups')
    if results.get('results') and results['results'][0].get('recordings'):
        LOGGER.info('AcoustID result found!')
        recordings = results['results'][0]['recordings']
        recording = max(recordings, key=lambda x: len(x.keys()))
        recording_id = recording['id']
        recording_artists = recording['artists']
        recording_title = recording['title']
        album_artist = recording_artists[0]['name']
        artist = ''.join([artist['name'] + artist.get('joinphrase', '') for artist in recording_artists])
        album = recording['releasegroups'][0]['title']

        return {'musicbrainz_releasetrackid': recording_id,
                'title': recording_title,
                'artist': artist,
                'albumartist': album_artist,
                'album': album}

    else:
        LOGGER.info('No AcoustID results found')
        return {}