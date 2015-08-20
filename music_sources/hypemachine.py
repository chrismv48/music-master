"""Extracts songs from hypemachine"""

from datetime import datetime

import hypem

from models.models import session

# extract songs based on popularity, genre or both
from models.models import QueuedTrack


def run():
    results = hypem.get_popular(filter='lastweek', page=1)
    tracks = []
    for track in results.data:
        date_posted = datetime.fromtimestamp(track.data['dateposted'])
        hours_delta = (datetime.now() - date_posted).total_seconds() / 60 / 60
        source_score = int(track.data['loved_count'] / hours_delta)
        hypem_row = QueuedTrack(title=track.data['title'],
                                 artist=track.data['artist'],
                                 year=date_posted.year,
                                 source='hypemachine',
                                 source_score=source_score,
                                 duration=track.data['time'])

        session.merge(hypem_row)

    session.commit()
    session.close()


if __name__ == '__main__':
    run()
