"""Main entry point to package"""
import argparse

from music_sources import hypemachine, reddit
from utils import run_file_listener, force_sync
import youtube_searcher, downloader

def main(arguments):

    run_file_listener()
    force_sync()

    if arguments.get_music:
        hypemachine.run()
        reddit.run()
        youtube_searcher.run()
        downloader.run()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--get_music', action='store_true', default=False)
    args = parser.parse_args()
    main(args)