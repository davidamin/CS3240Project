from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
import logging
import requests
import yaml
import os
import time


HOST = 'http://127.0.0.1:5000/'

WORKING_DIR = ""
SUID = ""


class OneDirFileHandles(FileSystemEventHandler):
    ## HANDLE ALL THINGS TO UPLOAD STUFF HERE!!!!!!!!
    def on_created(self, event):
        print "File has been created"

    def on_modified(self, event):
        print "File has been modified"

    def on_deleted(self, event):
        print "File has been deleted, everyone panic"

def new_user():
    print "Creating new account. Please fill out the following details:"
    username = raw_input('Username: ')
    password = hashlib.sha256(raw_input('Password: ')).hexdigest()
    confirm = hashlib.sha256(raw_input('Confirm Password: ')).hexdigest()


    if password == confirm :
        r = requests.get(HOST + "signup/" + username + "/" + password)
        print r.text

    init()

def sign_in():
    global WORKING_DIR
    global SUID
    print "Signing in. Please fill out the following details:"
    username = raw_input('Username: ')
    password = hashlib.sha256(raw_input('Password: ')).hexdigest()
    r = requests.get(HOST + "signin/" + username + "/" + password)
    result = yaml.load(r.text)
    if result[0] == "200":
        print "Successfully signed in! Please set up your local folder below: "
        WORKING_DIR = raw_input('Enter directory location for synchronized folder: ')
        SUID = result[1]
        WORKING_DIR = os.path.join(WORKING_DIR, 'OneDir')
        logging.debug("Making directory " + WORKING_DIR + " for User " + username )
        if os.path.exists(WORKING_DIR):
            logging.debug("Folder already exists!")
        else:
            os.mkdir(WORKING_DIR)
            logging.debug("Folder created!")
        runtime()
    elif result[0] == "401":
        print "ERROR: Password is incorrect! Please try again!"
        init()
    elif result[0] == "404":
        print "ERROR: Username was not found! Please try again!"
        init()

def runtime():
    print "Setup Complete: Intializing OneDir! Enjoy your day!"
    event_handler = OneDirFileHandles()
    observer = Observer()
    print WORKING_DIR
    #the recursive variable here determines whether the program watches subdirectories
    observer.schedule(event_handler, WORKING_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def init():
    print "Welcome to OneDir! Please Select from the following options!"
    print "0 : Create New Account!"
    print "1 : Sign into Account!"
    selection = int(raw_input("Option Selected: "))
    if selection == 0:
        print "hello"
    else:
        sign_in()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(filename='example.log',level=logging.DEBUG)
    init()



