__author__ = 'User'
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
#full disclosure, I only tried this on windows

#a simple event handler. It looks for any change to files in the folder given, or for the deletion in the folder given
#there are many more events to watch for, all documented in the Watchdog api if you need them
class CustomHandles(FileSystemEventHandler):
    def on_modified(self, event):
        print "File has been modified"

    def on_deleted(self, event):
        print "File has been deleted, everyone panic"

#this is essentially just the sample code from the watchdog website
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    #the program takes a command line argument, but we could easily change this to be the "Dropbox" folder for our program
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    path = "/Users/brian/Desktop"
    #the custom event handler watches everything and outputs it all, we need to write our own to take action on changes
    #event_handler = LoggingEventHandler()
    event_handler = CustomHandles()
    observer = Observer()
    #the recursive variable here determines whether the program watches subdirectories
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()