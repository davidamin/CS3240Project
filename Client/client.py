from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
import logging
import requests
import yaml
import os
import time
from Queue import *
from threading import Thread, Lock
import threading


# Things to do...
# 1) Threading loop on the command processing. DONE
# 2) Solve delete issues. Rooted to file naming issues.  DONE
# 3) Get error communication down pat? MOSTLY
# 4) Fix logging issues. MOSTLY

HOST = 'http://127.0.0.1:5000/'

WORKING_DIR = ""
SUID = ""
PROC_QUEUE = Queue()

def job_processor(name, stop_event):
    while (1):
        if stop_event.is_set():
            break
        elif PROC_QUEUE.empty() == False:
            try:
                job = PROC_QUEUE.get()
                logging.debug("PROCCESSING JOB " + job[0] + " ON  " + job[1])
                if job[0] == "Upload":
                    r = requests.post(HOST + "upload-file/" + SUID + secure_filepass(job[1]), files={'file': open(job[1], 'rb')})
                    result = yaml.load(r.text)
                    if result[0] == "200":
                        logging.debug("Uploaded file: " + secure_filepass(job[1]))
                    elif result[0] == "400":
                        logging.error("***Authentication Failure***")
                elif job[0] == "Delete":
                    r = requests.get(HOST + "delete-file/" + SUID + secure_filepass(job[1]))
                    result = yaml.load(r.text)
                    if result[0] == "200":
                        logging.debug("Deleted file: " + secure_filepass(job[1]))
                    elif result[0] == "400":
                        logging.error("***Authentication Failure***")
                elif job[0] == "New Dir":
                    r = requests.get(HOST + "new-dir/" + SUID + secure_filepass(job[1]))
                    result = yaml.load(r.text)
                    if result[0] == "200":
                        logging.debug("Directory Created: " + secure_filepass(job[1]))
                    elif result[0] == "400":
                        logging.error("***Authentication Failure***")
                elif job[0] == "Remove Dir":
                    r = requests.get(HOST + "delete-dir/" + SUID + secure_filepass(job[1]))
                    result = yaml.load(r.text)
                    if result[0] == "200":
                        logging.debug("Directory Created: " + secure_filepass(job[1]))
                    elif result[0] == "400":
                        logging.error("***Authentication Failure***")
                PROC_QUEUE.task_done()
            except:
                logging.error("ISSUE PERFORMING JOB")

        stop_event.wait(1)

def secure_filepass(filename):
    return filename.replace(WORKING_DIR,"")

class OneDirFileHandles(FileSystemEventHandler):
    ## HANDLE ALL THINGS TO UPLOAD STUFF HERE!!!!!!!!
    def on_created(self, event):
        if event.is_directory:
            logging.debug("Directory: " + event.src_path + " has been created locally.")

            PROC_QUEUE.put(("New Dir", event.src_path))
        else:
            logging.debug("File: " + event.src_path + " has been created locally.")

            PROC_QUEUE.put(("Upload", event.src_path))

    def on_modified(self, event):
        if event.is_directory:
            logging.debug("Directory: " + event.src_path + " has been modified locally.")

            PROC_QUEUE.put(("Remove Dir", event.src_path))
            PROC_QUEUE.put(("New Dir", event.src_path))
        else:
            logging.debug("File: " + event.src_path + " has been modified locally.")

            PROC_QUEUE.put(("Delete", event.src_path))
            PROC_QUEUE.put(("Upload", event.src_path))

    def on_deleted(self, event):
        if event.is_directory:
            logging.debug("Directory: " + event.src_path + " has been deleted locally.")

            PROC_QUEUE.put(("Remove Dir", event.src_path))
        else:
            logging.debug("File: " + event.src_path + " has been deleted locally.")

            PROC_QUEUE.put(("Delete", event.src_path))

def new_user():
    print "Creating new account. Please fill out the following details:"
    username = raw_input('Username: ')
    password = hashlib.sha256(raw_input('Password: ')).hexdigest()
    confirm = hashlib.sha256(raw_input('Confirm Password: ')).hexdigest()
    if password == confirm :
        r = requests.get(HOST + "signup/" + username + "/" + password)
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

def change_pass():
    print "To change password, please input"
    username = raw_input('Username: ')
    password = hashlib.sha256(raw_input('New Password: ')).hexdigest()
    r = requests.get(HOST + "changepass/" + username + "/" + password)
    result = yaml.load(r.text)

    if result[0] == "200":
        print "Password successfully changed!"
        init()
    else:
        print "ERROR: Username not found! Please try again!"
        init()

def user_stat():
    print "To see stats of user, please input"
    username = raw_input('Username: ')
    r = requests.get(HOST+"user-stat/"+username)
    result = yaml.load(r.text)

    if result [0] == "400":
        logging.debug("Unsucessful retrieval of " + username + " stats")
        print "Unsuccesful retrieval of " + username + " stats"
    else:
        logging.debug("Succesfully retrieved " + username + " stats")
        print "Succesfully retrieved " + username + " stats"





def runtime():
    print "Setup Complete: Intializing OneDir! Enjoy your day!"
    event_handler = OneDirFileHandles()
    observer = Observer()
    print WORKING_DIR

    #the recursive variable here determines whether the program watches subdirectories
    observer.schedule(event_handler, WORKING_DIR, recursive=True)
    observer.start()
    stop = threading.Event()
    th = Thread(target=job_processor, args=("Thread",stop))
    th.setDaemon(True)
    th.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        stop.set()
    observer.join()
    th.join()

def init():
    print "Welcome to OneDir! Please Select from the following options!"
    print "0 : Create New Account!"
    print "1 : Sign into Account!"
    print "2 : Change my password!"
    selection = int(raw_input("Option Selected: "))
    if selection == 0:
        new_user()
    elif selection == 2:
        change_pass()
    else:
        sign_in()

if __name__ == '__main__':
    logging.basicConfig(filename='Server_Log.log',level=logging.DEBUG)
    # logging.basicConfig(filename='example.log',level=logging.DEBUG)
    init()



