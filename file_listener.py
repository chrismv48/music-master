"""Docstring goes here"""
import sys
from config import LOGGER, TRACK_DIRECTORY
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from file_trigger import sync_file

reload(sys)
sys.setdefaultencoding("utf-8")


class MyHandler(PatternMatchingEventHandler):
    patterns = ['*.mp3']
    ignore_patterns = ['*/holding*']
    ignore_directories = True
    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        track_path = event.dest_path if event.event_type == 'moved' else event.src_path
        LOGGER.info('File change detected: {event_type}: {track_path}'.format(event_type=event.event_type,
                                                                              track_path=track_path))
        if '/Users/carmstrong/Projects/music_master/tracks/holding' in track_path:
            LOGGER.info('Protected path, will make no changes!!')
        sync_file(track_path, event.event_type)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)


if __name__ == '__main__':
    observer = Observer()
    observer.schedule(MyHandler(), path=TRACK_DIRECTORY, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
