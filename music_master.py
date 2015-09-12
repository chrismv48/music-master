"""Main entry point to package"""

from music_sources import hypemachine, reddit
import youtube_searcher, downloader

def run():

    hypemachine.run()
    reddit.run()
    youtube_searcher.run()
    downloader.run()

if __name__ == '__main__':
    run()