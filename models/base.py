"""Database models for the Blacklist API."""

# Standard library imports
import json
import datetime

# Third-party imports
import arrow
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from utils import clean_search_term


class SerializedModel(object):
    """A SQLAlchemy model mixin class that can serialize itself as JSON."""

    @property
    def table_fields(self):
        return [key for key in self.__table__.columns.keys() if not key.startswith('_')]


    def as_dict(self):
        """Return dict representation of class by iterating over database
        columns."""
        value = {}
        for column in self.__table__.columns:
            attribute = getattr(self, column.name)
            if isinstance(attribute, datetime.datetime):
                attribute = arrow.get(attribute, 'US/Eastern').isoformat()
            value[column.name] = attribute
        return value

    def from_dict(self, attributes):
        """Update the current instance based on attribute->value items in
        *attributes*."""
        for attribute in attributes:
            if attribute in self.table_fields:
                setattr(self, attribute, attributes[attribute])
        return self

    def as_json(self):
        """Return JSON representation taken from dict representation."""
        return json.dumps(self.as_dict())

def default_album_artist(context):
    return context.current_parameters['artist']


class TrackBase(object):
    title = Column(String(convert_unicode=True))
    artist = Column(String(convert_unicode=True))
    album_artist = Column(String(convert_unicode=True), default=default_album_artist)
    album = Column(String(convert_unicode=True))
    source = Column(String)
    source_score = Column(Integer, default=None)
    musicbrainz_releasetrackid = Column(String)  # this should be set to unique, but merge doesn't seem to work when
    # unique keys are used
    danceability = Column(Integer, default=None)
    energy = Column(Integer, default=None)
    valence = Column(Integer, default=None)
    tempo = Column(Integer, default=None)
    duration = Column(Integer, default=None)
    liveness = Column(Integer, default=None)
    acousticness = Column(Integer, default=None)
    speechiness = Column(Integer, default=None)
    genres = Column(String)
    year = Column(String(4))
    youtube_video_id = Column(String)
    youtube_video_title = Column(String(convert_unicode=True))
    last_searched_acoustid = Column(DateTime, default=None)
    last_searched_echonest = Column(DateTime, default=None)
    created_on = Column(DateTime, default=func.now())
    last_modified = Column(DateTime, default=func.now(),
                           onupdate=func.now())

    @validates('energy', 'valence')
    def convert_strings_to_int(self, key, field):
        if isinstance(field, unicode) or isinstance(field, str):
            try:
                return int(field)
            except ValueError:
                return None
        else:
            return field

    @validates('energy', 'valence', 'danceability', 'liveness', 'acousticness', 'speechiness')
    def validate_metrics(self, key, field):
        if isinstance(field, float):
            if field <= 1:
                return int(field)

        return field

    @hybrid_property
    def search_phrase(self):
        return clean_search_term(self.album_artist + ' ' + self.title)

    def __repr__(self):
        return u"<{}>({})>".format(self.__class__.__name__, self.artist + ' ' + self.title)

