"""Main entry point to package"""
import argparse

from music_sources import hypemachine, reddit
from library_v2 import sync_library
import youtube_searcher, downloader

def main(arguments):

    if arguments.get_music:
        hypemachine.run()
        reddit.run()
        youtube_searcher.run()
        downloader.run()

    sync_library()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--get_music', action='store_true', default=False)
    args = parser.parse_args()
    main(args)