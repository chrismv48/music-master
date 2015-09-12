"""Extracts songs from hypemachine"""

from datetime import datetime

import hypem
from config import LOGGER

from models.models import session

# extract songs based on popularity, genre or both
from models.models import QueuedTrack


def run():
    LOGGER.info('Getting music from HypeMachine...')
    results = hypem.get_popular(filter='lastweek', page=1)
    LOGGER.info('Found {} tracks, merging to database...' .format(len(results.data)))
    try:
        for track in results.data:
            date_posted = datetime.fromtimestamp(track.data['dateposted'])
            #TODO: this is unpredictable because there are random postid's returned with different loved and
            # dateposted values
            hours_delta = (datetime.now() - date_posted).total_seconds() / 60 / 60
            source_score = int(track.data['loved_count'] / hours_delta)
            hypem_row = QueuedTrack(title=track.data['title'],
                                    artist=track.data['artist'],
                                    year=date_posted.year,
                                    source='hypemachine',
                                    source_score=source_score,
                                    duration=track.data['time'])

            session.merge(hypem_row)
    except:
        raise

    finally:
        session.commit()
        LOGGER.info('Merge completed.')


if __name__ == '__main__':
    run()
