"""Scrape songs from Reddit"""

import praw
import re

client = praw.Reddit(user_agent='song_finder')

subbreddits = ['listentothis']

subreddit = client.get_subreddit(subbreddits[0])

top_posts = subreddit.get_top_from_week()

post = top_posts.next()

post_comments = post.comments
post_score = post.score
post_date = post.created_utc
# post title syntax: Artist -- Title [Genre(s)] (Year)
post_title = post.title
post_flair = post.link_flair_text
post_url = post.url
post_domain = post.domain
post_hint = post.post_hint
post_num_comments = post.num_comments


def parse_post_title(post_title):
    results = {"artist": re.search('(.*) --', post_title),
               "title": re.search('-- (.*) \[', post_title),
               "year": re.search('\((\d{4})\)', post_title),
               "genre": re.search('\[(.*)\]', post_title)}

    for k, v in results.iteritems():
        if v:
            results[k] = v.groups()[0].strip()
        else:
            results.pop(k)
