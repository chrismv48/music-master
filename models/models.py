import datetime
import hashlib
import os
from mutagen.easyid3 import EasyID3
from EasyID3Patched import EasyID3Patched
from base import SerializedModel, TrackBase
from sqlalchemy import Column, String, Integer, DateTime, Date, Boolean, event, create_engine, func, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker, validates, scoped_session

from utils import clean_search_term

engine = create_engine("postgresql+psycopg2://carmstrong@localhost/music_master")
Session = sessionmaker(bind=engine, expire_on_commit=True)
session = scoped_session(Session)
Base = declarative_base()

def create_tables():
    Base.metadata.create_all(bind=engine)

def fingerprint_md5(context):
    return hashlib.md5(context.current_parameters['fingerprint']).hexdigest()


class QueuedTrack(SerializedModel, TrackBase, Base):
    __tablename__ = "queued_track"

    title = Column(String(convert_unicode=True), primary_key=True)
    artist = Column(String(convert_unicode=True), primary_key=True)


class SavedTrack(TrackBase, SerializedModel, Base):
    __tablename__ = 'saved_track'

    #track_hash = Column(String, primary_key=True, default=fingerprint_md5)
    fingerprint = Column(String, nullable=False, primary_key=True)
    path = Column(String(convert_unicode=True), primary_key=True)
    md5 = Column(String, default=None)
    play_count = Column(Integer, default=0)
    rating = Column(Integer, default=None)

    @hybrid_property
    def filename(self):
        return os.path.basename(self.path)

    @hybrid_property
    def search_phrase(self):
        return clean_search_term(self.album_artist + ' ' + str(self.title) if all([self.album_artist, self.title]) else
                                     self.filename)

    def __repr__(self):
        return u"<{}>({})>".format(self.__class__.__name__, self.search_phrase)


class DeletedTrack(SerializedModel, TrackBase, Base):
    __tablename__ = "deleted_track"

    track_hash = Column(String, primary_key=True, default=fingerprint_md5)
    fingerprint = Column(String, nullable=False)
    path = Column(String(convert_unicode=True), primary_key=True)
    md5 = Column(String, default=None)
    play_count = Column(Integer, default=0)
    rating = Column(Integer, default=None)

    @hybrid_property
    def filename(self):
        return os.path.basename(self.path)

    @hybrid_property
    def search_phrase(self):
        return clean_search_term(self.album_artist + ' ' + self.title if all([self.album_artist, self.title]) else
                                     self.filename)

    def __repr__(self):
        return u"<{}>({})>".format(self.__class__.__name__, self.search_phrase)



# @event.listens_for(SavedTrack, 'after_insert')
# @event.listens_for(SavedTrack, 'after_update')
# def after_insert_update_listener(mapper, connection, target):
#     from enricher_v3 import enrich_track # avoid circular dependency
#     print 'Model {} updated, let\'s update the file'.format(target)
#     target = enrich_track(target)
#     easyID3_track = EasyID3Patched(target.path)
#     easyID3_track.update_from_dict(target.as_dict())
#     if easyID3_track.is_modified:
#         easyID3_track.save()
#     print 'Finished'


