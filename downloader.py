# coding=utf-8

"""Downloads eligible tracks"""
import os
import sys

from acoustid import fingerprint_file

reload(sys)
sys.setdefaultencoding("utf-8")

from models.models import QueuedTrack, SavedTrack, session
import youtube_dl
from utils import calculate_md5
from config import TRACK_DIRECTORY, LOGGER

HOLD_DIRECTORY = TRACK_DIRECTORY + 'holding/'


def get_tracks_to_download():
    """Returns ORM for tracks that have no youtube_video_id"""
    tracks_to_download = session.query(QueuedTrack).filter(QueuedTrack.youtube_video_id != None).all()

    return tracks_to_download


def build_download_link(youtube_video_id):
    """Returns a full youtube link given the youtube_video_id"""
    youtube_base_link = "https://www.youtube.com/watch?v="
    return unicode(youtube_base_link + youtube_video_id)


def run():
    # TODO: break this into smaller functions
    LOGGER.info('Running music downloader...')
    tracks_to_download = get_tracks_to_download()
    if not tracks_to_download:
        LOGGER.info('No queued tracks found in database')
        return
    LOGGER.info('Found {} tracks from database to download...'.format(len(tracks_to_download)))
    options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False}

    for queued_track in tracks_to_download:
        exists = session.query(SavedTrack).filter(SavedTrack.artist == queued_track.artist,
                                                  SavedTrack.title == queued_track.title).count() > 0
        if exists:
            LOGGER.info('Track already exists as Saved Track, deleting Queued track and skipping download.')
            session.delete(queued_track)
            session.commit()
            continue
        track_save_name = u'{} - {}'.format(queued_track.artist, queued_track.title)
        final_track_path = TRACK_DIRECTORY + track_save_name + '.mp3'
        holding_track_path = HOLD_DIRECTORY + track_save_name + '.mp3'
        LOGGER.info('Downloading track: {}'.format(track_save_name))
        options['outtmpl'] = u'{}/{}.%(ext)s'.format(HOLD_DIRECTORY, track_save_name)
        ydl = youtube_dl.YoutubeDL(options)
        download_link = build_download_link(queued_track.youtube_video_id)
        # download the track
        try:
            ydl.download([download_link])
        except youtube_dl.utils.DownloadError as e:
            LOGGER.warning('youtube-dl encountered an error: {}' .format(e.message))
            continue
        # TODO: might need to create a holding directory so watchdog doesn't overwrite the below
        saved_track = SavedTrack()
        saved_track.update_from_dict(queued_track.as_dict())
        saved_track.path = final_track_path
        saved_track.md5 = calculate_md5(holding_track_path)
        fingerprint_duration = fingerprint_file(holding_track_path, 30)
        saved_track.fingerprint = fingerprint_duration[1]
        saved_track.duration = fingerprint_duration[0]

        session.merge(saved_track)
        session.delete(queued_track)
        session.commit()
        os.rename(holding_track_path, final_track_path)
        LOGGER.info('Complete. Downloaded track data committed to database.')


if __name__ == '__main__':
    run()
