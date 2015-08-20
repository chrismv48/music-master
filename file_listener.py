"""Docstring goes here"""
import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from file_trigger import file_change_trigger
reload(sys)
sys.setdefaultencoding("utf-8")

class MyHandler(PatternMatchingEventHandler):
    patterns=["*.mp3"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        print event.src_path
        print event.event_type
        track_path = event.dest_path if event.event_type == 'moved' else event.src_path
        file_change_trigger(track_path)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        #TODO: add additional processes for new files?
        self.process(event)

    def on_moved(self, event):
        self.process(event)

if __name__ == '__main__':
    args = sys.argv[1:]
    observer = Observer()
    observer.schedule(MyHandler(), path=args[0] if args else '.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    except Exception as e:
        print e

    observer.join()