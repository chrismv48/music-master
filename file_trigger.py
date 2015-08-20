"""Docstring goes here"""
import acoustid
from datetime import timedelta, datetime

from EasyID3Patched import EasyID3Patched
from config import ACOUST_ID_API_KEY, LOGGER
from enricher import enrich_track
from models.models import SavedTrack, session


def load_track_with_fingerprint(track_path):
    LOGGER.info('Loading track...')
    easyID3_track = EasyID3Patched(track_path)
    if not all([easyID3_track.get('acoustid_fingerprint'), easyID3_track.get('length')]):
        LOGGER.info('No fingerprint; generating from AcoustID')
        duration, fingerprint = acoustid.fingerprint_file(track_path, 30)
        easyID3_track['length'], easyID3_track['acoustid_fingerprint'] = unicode(duration), unicode(fingerprint)
    return easyID3_track


def file_change_trigger(track_path):
    easyID3_track = load_track_with_fingerprint(track_path)
    saved_track = session.query(SavedTrack).filter(SavedTrack.fingerprint == easyID3_track.model_dict[
    'fingerprint']).first()
    if not saved_track:
        saved_track = SavedTrack()
        LOGGER.info('Track not found in database; creating...')
    else:
        LOGGER.info('Track found in database:')
        LOGGER.info(saved_track)
    if not saved_track.last_searched_acoustid or saved_track.last_searched_acoustid < (
            saved_track.last_searched_acoustid - timedelta(days=7)):
        LOGGER.info('Doing AcoustID lookup for track data...')
        acoustid_data = acoustid_lookup(easyID3_track.model_dict['fingerprint'],
                                        int(easyID3_track.model_dict['duration']))
        easyID3_track.update_from_dict(acoustid_data)
        saved_track.last_searched_acoustid = datetime.now()

    saved_track.from_dict(easyID3_track.model_dict)
    enrich_track(saved_track, do_commit=True)

    if session.is_modified(saved_track):
        session.merge(saved_track)
        session.commit()

    if easyID3_track.is_modified:
        easyID3_track.save()


def acoustid_lookup(fingerprint, duration):
    results = acoustid.lookup(ACOUST_ID_API_KEY, fingerprint, duration, meta='recordings + releasegroups')
    if results['results'] and results['results'][0].get('recordings'):
        LOGGER.info('AcoustID result found!')
        recording = results['results'][0]['recordings'][0]
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