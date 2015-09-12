"""Scrape songs from Reddit"""

import praw
import re
from datetime import datetime
from models.models import QueuedTrack, session


def parse_post_title(post_title):
    # post title syntax: Artist -- Title [Genre(s)] (Year)
    print post_title
    results = {"artist": re.search('(.*) --', post_title),
               "title": re.search('-- (.*) \[', post_title),
               "year": re.search('\((\d{4})\)', post_title)}

    for k, v in results.iteritems():
        if v:
            results[k] = v.groups()[0].strip()
        else:
            return None
    return results


def run():
    client = praw.Reddit(user_agent='song_finder')

    subbreddits = ['listentothis']

    subreddit = client.get_subreddit(subbreddits[0])

    top_posts = subreddit.get_top_from_week()

    for post in top_posts:

        track_dict = parse_post_title(post.title)
        if not track_dict:
            continue
        date_posted = datetime.fromtimestamp(post.created_utc)
        hours_delta = (datetime.now() - date_posted).total_seconds()
        source_score = int(post.score) / hours_delta * 100.0
        track_dict.update({'genres': post.link_flair_text,
                           'source_score': source_score,
                           'source': 'reddit - listentothis'})

        queued_track = QueuedTrack(**track_dict)

        session.merge(queued_track)

    session.commit()

if __name__ == '__main__':
    run()