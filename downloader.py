# coding=utf-8

"""Downloads eligible tracks"""
import sys

from acoustid import fingerprint_file

reload(sys)
sys.setdefaultencoding("utf-8")

from models.models import QueuedTrack, SavedTrack, session
import youtube_dl
from utils import create_or_modify_orm, calculate_md5
from config import TRACK_DIRECTORY


def get_tracks_to_download():
    """Returns ORM for tracks that have no youtube_video_id"""
    tracks_to_download = session.query(QueuedTrack).filter(QueuedTrack.youtube_video_id != None).all()

    return tracks_to_download


def build_download_link(youtube_video_id):
    """Returns a full youtube link given the youtube_video_id"""
    youtube_base_link = "https://www.youtube.com/watch?v="
    return unicode(youtube_base_link + youtube_video_id)

def run():
    #TODO: break this into smaller functions

    tracks_to_download = get_tracks_to_download()

    options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False}

    try:
        for queued_track in tracks_to_download:
                track_filename = u'{} - {}'.format(queued_track.artist, queued_track.title)
                options['outtmpl'] = u'{}/{}.%(ext)s'.format(TRACK_DIRECTORY, track_filename)
                ydl = youtube_dl.YoutubeDL(options)
                track_path = TRACK_DIRECTORY + track_filename + '.mp3'
                download_link = build_download_link(queued_track.youtube_video_id)
                ydl.download([download_link])
                track_model = create_or_modify_orm(queued_track.__dict__, SavedTrack())
                track_model.path = track_path
                track_model.md5 = calculate_md5(track_path)
                track_model.fingerprint = fingerprint_file(track_path)
                session.add(track_model)
                session.delete(queued_track)
    except:
        raise

    finally:
        session.commit()
        session.close()

if __name__ == '__main__':

    run()