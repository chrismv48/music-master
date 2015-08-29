"""Main entry point to package"""

from music_sources import hypemachine
import youtube_searcher, downloader

def run():

    hypemachine.run()
    youtube_searcher.run()
    downloader.run()

if __name__ == '__main__':
    run()