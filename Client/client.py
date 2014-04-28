from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.utils import dirsnapshot
import hashlib
import logging
import requests
import yaml
import os
import time
import urllib2
from Queue import *
from threading import Thread, Lock
import threading
import pickle



HOST = 'http://172.25.208.188:5000/'
#HOST = 'http://0.0.0.0:5000/'
WORKING_DIR = ""
SUID = ""
PROC_QUEUE = Queue()
TIME_STAMP = ""
DIR_SNAPSHOT = dirsnapshot.DirectorySnapshot
SYNCRHONIZED = True


def job_processor(name, stop_event):
    #global SYNCRHONIZED
    SAVE = False
    while (1):
        if stop_event.is_set():
            break
        elif PROC_QUEUE.empty() == False:
            if SYNCRHONIZED == True:
                try:
                    job = PROC_QUEUE.get()
                    #SAVE = False
                    logging.debug("PROCCESSING JOB " + job[0] + " ON  " + job[1])
                    if job[0] == "Upload":
                        r = requests.post(HOST + "upload-file/" + SUID + secure_filepass(job[1]), files={'file': open(job[1], 'rb')})
                        result = yaml.load(r.text)
                        if result[0] == "200":
                            logging.debug("Uploaded file: " + secure_filepass(job[1]))
                            SAVE = True
                        elif result[0] == "400":
                            logging.error("***Authentication Failure***")
                    elif job[0] == "Delete":
                        r = requests.get(HOST + "delete-file/" + SUID + secure_filepass(job[1]))
                        result = yaml.load(r.text)
                        if result[0] == "200":
                            SAVE = True
                            logging.debug("Deleted file: " + secure_filepass(job[1]))
                        elif result[0] == "400":
                            logging.error("***Authentication Failure***")
                    elif job[0] == "New Dir":
                        r = requests.get(HOST + "new-dir/" + SUID + secure_filepass(job[1]))
                        result = yaml.load(r.text)
                        if result[0] == "200":
                            SAVE = True
                            logging.debug("Directory Created: " + secure_filepass(job[1]))
                        elif result[0] == "400":
                            logging.error("***Authentication Failure***")
                    elif job[0] == "Remove Dir":
                        r = requests.get(HOST + "delete-dir/" + SUID + secure_filepass(job[1]))
                        result = yaml.load(r.text)
                        if result[0] == "200":
                            SAVE = True
                            logging.debug("Directory Created: " + secure_filepass(job[1]))
                        elif result[0] == "400":
                            logging.error("***Authentication Failure***")
                    elif job[0] == "Download":
                        SAVE = False
                        logging.debug("Starting download")
                        r = urllib2.urlopen(HOST + "download-file/" + SUID + secure_filepass(job[1]))
                        print "hello"
                        print os.path.join(WORKING_DIR, job[1])
                        with open(os.path.join(WORKING_DIR, job[1]), 'wb') as f:
                            #print "hello"
                            f.write(r.read())

                    PROC_QUEUE.task_done()

                except:
                    logging.error("ISSUE PERFORMING JOB")

        elif PROC_QUEUE.empty() == True & SAVE == True:
            if  SYNCRHONIZED == True:
                SAVE = False
                logging.debug("New Snapshot required....")
                global TIME_STAMP
                global DIR_SNAPSHOT

                DIR_SNAPSHOT = dirsnapshot.DirectorySnapshot(WORKING_DIR, recursive=True)
                file_write = file("./client_SAVEFILE", 'w')
                yaml.dump((WORKING_DIR,SUID,TIME_STAMP,DIR_SNAPSHOT),file_write)
                #send = pickle.dumps(DIR_SNAPSHOT)
                # Change this line.. Once it's correct.
                r = requests.get(HOST + "snapshot/" + SUID)
                result = yaml.load(r.text)
                if result[0] == "200":
                    logging.debug("Snapshot saved. Timestamp updated to: " + result[1])
                    TIME_STAMP = result[1]
                elif result[0] == "400":
                    logging.error("***Authentication Failure***")
        else:
            server_sync()
            local_sync()
            stop_event.wait(2)

        # stop_event.wait(1)

def secure_filepass(filename):
    return filename.replace(WORKING_DIR,"")

def server_sync():
    global TIME_STAMP
    temp_TIME_STAMP = ""
    r = requests.get(HOST + "timestamp/" + SUID)
    result = yaml.load(r.text)
    if result[0] == "200":
        print TIME_STAMP + " " + result[1]
        temp_TIME_STAMP = TIME_STAMP
        if TIME_STAMP != result[1]:
            logging.debug("TIME STAMP NO LONGER SAME....... NEED TO DOWNLOAD")
            if (TIME_STAMP == ''):
                r = requests.post(HOST + "get-snapshot/" + SUID,data='new')
            else:
                r = requests.post(HOST + "get-snapshot/" + SUID, data=TIME_STAMP)
            result = yaml.load(r.text)

            if result[0] == "200":
                # server_snap = pickle.loads(result[1])
                # paths_given = []
                # ONCE = False
                # ROOT = ""
                # for path in server_snap.paths:
                #     # print path
                #     paths_given.append(path)
                # paths = sorted(paths_given)
                # for path in paths:
                #     if ONCE:
                #         path = path.replace(ROOT, WORKING_DIR)
                #         if os.path.exists(path) == False:
                #             # print path
                #             logging.debug("Checking if " + path + " is a directory...")
                #             r = requests.get(HOST + "is-dir/" + SUID + secure_filepass(path))
                #             result = yaml.load(r.text)
                #             if result[0] == "200":
                #                 if result[1]:
                #                     logging.debug("Directory")
                #                     os.makedirs(path)
                #                 else:
                #                     logging.debug("File")
                #                     PROC_QUEUE.put(("Download", path))
                #             elif result[0] == "400":
                #                 logging.error("***Authentication Failure***")
                #         else:
                #             logging.debug("File or Directory Exists... Assigning Timestamp")
                #             TIME_STAMP = temp_TIME_STAMP
                #
                #     else:
                #         ONCE = True
                #         ROOT = path
                #         print "ROOT: " + ROOT

                server_dir = result[1]
                snap_diff = pickle.loads(result[2])
                TIME_STAMP = result[3]

                for dir in snap_diff.dirs_created:
                    logging.debug("Directory: " + dir.replace(server_dir,"") + " has been created remotely.")

                    os.mkdir(dir.replace(server_dir,WORKING_DIR))

                for dir in snap_diff.dirs_deleted:
                    logging.debug("Directory: " + dir + " has been deleted remotely.")

                    os.removedirs(dir.replace(server_dir,WORKING_DIR))

                for dir in snap_diff.dirs_modified:
                    logging.debug("Directory: " + dir + " has been modified remotely.")

                for dir in snap_diff.dirs_moved:
                    logging.debug("Directory: " + dir[0] + " has been RENAMED remotely.")

                    os.rename(dir[0].replace(server_dir,WORKING_DIR),dir[1].replace(server_dir,WORKING_DIR))

                for file2 in snap_diff.files_created:
                    logging.debug("File: " + file2 + " has been created remotely.")

                    PROC_QUEUE.put(("Download", file2.replace(server_dir,WORKING_DIR)))

                for file2 in snap_diff.files_deleted:
                    logging.debug("File: " + file2 + " has been deleted remotely.")

                    os.remove(file2.replace(server_dir,WORKING_DIR))

                for file2 in snap_diff.files_modified:
                    logging.debug("File: " + file2 + " has been modified remotely.")
                    #temp = file.replace(server_dir,WORKING_DIR)
                    os.remove(file2.replace(server_dir,WORKING_DIR))
                    PROC_QUEUE.put(("Download", file2.replace(server_dir,WORKING_DIR)))

                for file2 in snap_diff.files_moved:
                    logging.debug("File: " + file2[0] + " has been RENAMED remotely.")

                    os.rename(file2[0].replace(server_dir,WORKING_DIR),file2[1].replace(server_dir,WORKING_DIR))

                DIR_SNAPSHOT = dirsnapshot.DirectorySnapshot(WORKING_DIR, recursive=True)
                file_write = file("./client_SAVEFILE", 'w')
                yaml.dump((WORKING_DIR,SUID,TIME_STAMP,DIR_SNAPSHOT),file_write)

            elif result[0] == "400":
                logging.error("***Authentication Failure***")
    elif result[0] == "401":
        logging.debug("No time stamp yet.... New account")
    elif result[0] == "400":
        logging.error("***Authentication Failure***")

def local_sync():
    TEMP_SNAPSHOT = dirsnapshot.DirectorySnapshot(WORKING_DIR, recursive=True)

    diff = dirsnapshot.DirectorySnapshotDiff(DIR_SNAPSHOT,TEMP_SNAPSHOT)

    for dir in diff.dirs_created:
        logging.debug("Directory: " + dir + " has been created locally.")

        PROC_QUEUE.put(("New Dir", dir))

    for dir in diff.dirs_deleted:
        logging.debug("Directory: " + dir + " has been deleted locally.")

        PROC_QUEUE.put(("Remove Dir", dir))

    for dir in diff.dirs_modified:
        logging.debug("Directory: " + dir + " has been modified locally.")

        PROC_QUEUE.put(("Remove Dir", dir))
        PROC_QUEUE.put(("New Dir", dir))

    for dir in diff.dirs_moved:
        logging.debug("Directory: " + dir[0] + " has been RENAMED locally.")

        PROC_QUEUE.put(("Remove Dir", dir[0]))
        PROC_QUEUE.put(("New Dir", dir[1]))

    for file in diff.files_created:
        logging.debug("File: " + file + " has been created locally.")

        PROC_QUEUE.put(("Upload", file))

    for file in diff.files_deleted:
        logging.debug("File: " + file + " has been deleted locally.")

        PROC_QUEUE.put(("Delete", file))

    for file in diff.files_modified:
        logging.debug("File: " + file + " has been modified locally.")

        PROC_QUEUE.put(("Delete", file))
        PROC_QUEUE.put(("Upload", file))

    for file in diff.files_moved:
        logging.debug("File: " + file[0] + " has been RENAMED locally.")

        PROC_QUEUE.put(("Delete", file[0]))
        PROC_QUEUE.put(("Upload", file[1]))



#class OneDirFileHandles(FileSystemEventHandler):

    # def on_created(self, event):
    #     # if event.is_directory:
    #     #     logging.debug("Directory: " + event.src_path + " has been created locally.")
    #     #
    #     #     PROC_QUEUE.put(("New Dir", event.src_path))
    #     # else:
    #     #     logging.debug("File: " + event.src_path + " has been created locally.")
    #     #
    #     #     PROC_QUEUE.put(("Upload", event.src_path))
    #
    # def on_modified(self, event):
    #     if event.is_directory:
    #         logging.debug("Directory: " + event.src_path + " has been modified locally.")
    #
    #         PROC_QUEUE.put(("Remove Dir", event.src_path))
    #         PROC_QUEUE.put(("New Dir", event.src_path))
    #     else:
    #         logging.debug("File: " + event.src_path + " has been modified locally.")
    #
    #         PROC_QUEUE.put(("Delete", event.src_path))
    #         PROC_QUEUE.put(("Upload", event.src_path))
    #
    # def on_moved(self,event):
    #     if event.is_directory:
    #         logging.debug("Directory: " + event.src_path + " has been modified locally.")
    #
    #         PROC_QUEUE.put(("Remove Dir", event.src_path))
    #         PROC_QUEUE.put(("New Dir", event.dest_path))
    #     else:
    #         logging.debug("File: " + event.src_path + " has been modified locally.")
    #
    #         PROC_QUEUE.put(("Delete", event.src_path))
    #         PROC_QUEUE.put(("Upload", event.dest_path))
    #
    # def on_deleted(self, event):
    #     if event.is_directory:
    #         logging.debug("Directory: " + event.src_path + " has been deleted locally.")
    #
    #         PROC_QUEUE.put(("Remove Dir", event.src_path))
    #     else:
    #         logging.debug("File: " + event.src_path + " has been deleted locally.")
    #
    #         PROC_QUEUE.put(("Delete", event.src_path))

def new_user():
    print "Creating new account. Please fill out the following details:"
    username = raw_input('Username: ')
    password = hashlib.sha256(raw_input('Password: ')).hexdigest()
    confirm = hashlib.sha256(raw_input('Confirm Password: ')).hexdigest()
    if password == confirm :
        r = requests.get(HOST + "signup/" + username + "/" + password)
        result = yaml.load(r.text)
    init()

def sign_in():
    global WORKING_DIR
    global SUID
    global TIME_STAMP
    global DIR_SNAPSHOT
    print "Signing in. Please fill out the following details:"
    username = raw_input('Username: ')
    password = hashlib.sha256(raw_input('Password: ')).hexdigest()
    r = requests.get(HOST + "signin/" + username + "/" + password)
    result = yaml.load(r.text)
    if result[0] == "200" and not username == "admin":
        print "Successfully signed in! Please set up your local folder below: "
        WORKING_DIR = raw_input('Enter directory location for synchronized folder: ')
        SUID = result[1]
        WORKING_DIR = os.path.join(WORKING_DIR, 'OneDir')
        logging.debug("Making directory " + WORKING_DIR + " for User " + username )
        if os.path.exists(WORKING_DIR):
            logging.debug("Folder already exists!")
            if(os.path.exists(os.path.join(WORKING_DIR,"shared"))):
                logging.debug("Shared folder already exists!")
            else:
                os.mkdir(os.path.join(WORKING_DIR,"shared"))
        else:
            os.mkdir(WORKING_DIR)
            os.mkdir(os.path.join(WORKING_DIR,"shared"))
            logging.debug("Folder created!")

        DIR_SNAPSHOT = dirsnapshot.DirectorySnapshot(WORKING_DIR, recursive=True)
        file_write = file("./client_SAVEFILE", 'w')
        yaml.dump((WORKING_DIR,SUID,TIME_STAMP,DIR_SNAPSHOT),file_write)

        runtime()
    elif result[0] == "200" and username == "admin":
        print "Signed in to admin account."
        SUID = result[1]
        admin_menu()
    elif result[0] == "401":
        print "ERROR: Password is incorrect! Please try again!"
        init()
    elif result[0] == "404":
        print "ERROR: Username was not found! Please try again!"
        init()

#somehow need to give the users and admins the option to do this after sign in
def change_pass():
    print "To change password, please input"
    username = raw_input('Username: ')
    oldpass = hashlib.sha256(raw_input('Old Password: ')).hexdigest()
    password = hashlib.sha256(raw_input('New Password: ')).hexdigest()
    r = requests.get(HOST + "signin/" + username + "/" + oldpass)
    result = yaml.load(r.text)
    if result[0] == "200":
        SUID = result[1]
    elif result[0] == "401":
        print "ERROR: Password is incorrect! Please try again!"
        init()
    elif result[0] == "404":
        print "ERROR: Username was not found! Please try again!"
        init()

    r = requests.get(HOST + "changepass/" + username + "/" + password + "/" + SUID)
    result = yaml.load(r.text)

    if result[0] == "200":
        print "Password successfully changed!"
        init()
    else:
        print "ERROR: Username not found! Please try again!"
        init()

def admin_change_pass():
    print "To change user's password, please input"
    username = raw_input('Username: ')
    password = hashlib.sha256(raw_input('New Password: ')).hexdigest()

    r = requests.get(HOST + "changepass/" + username + "/" + password + "/" + SUID)
    result = yaml.load(r.text)

    if result[0] == "200":
        print "Password successfully changed!"
    else:
        print "ERROR: Username not found! Please try again!"

def user_stat():
    #print "To see stats of user, please input"
    #username = raw_input('Username: ')
    r = requests.get(HOST+"userstat")
    result = yaml.load(r.text)

    if result[0] == "400":
        logging.debug("Unsucessful retrieval of  users stats")
        print "Unsuccesful retrieval of user stats"
    elif result[0] == "200":
        logging.debug("Succesfully retrieved users stats")
        print "Succesfully retrieved users stats"
        print result[1]
    else:
        logging.debug("Succesfully retrieved users stats")
        print "Succesfully retrieved users stats"

def synchronize():
    global SYNCRHONIZED
    if SYNCRHONIZED:
        print "To turn off Autosync, enter y:"
        selection = str(raw_input("> "))
        if selection == "y":
            SYNCRHONIZED = False
    else:
        print "To turn on Autosync, enter y:"
        selection = str(raw_input("> "))
        if selection == "y":
            SYNCRHONIZED = True

def remove_user():
    print "To permanently remove a user, please input"
    username = raw_input('Username: ')
    delfiles = raw_input('Delete files too? 1 for yes, 0 for no: ')
    r = requests.get(HOST+"remove_user/"+username + "/" + delfiles)
    result = yaml.load(r.text)

    if result [0] == "400":
        logging.debug("Couldn't remove " + username)
        print "Couldn't remove " + username + "."
    else:
        logging.debug("Succesfully removed " + username)
        print "Succesfully removed " + username + "."



def admin_menu():
    print "Welcome to OneDir! Please Select from the following options!"
    print "0 : View Users on Server"
    print "1 : View Statistics for Server"
    print "2 : View Connection Log"
    print "3 : Remove a User"
    print "4 : Change a User's Password"
    selection = int(raw_input("Option Selected: "))
    if selection == 0:
        view_report()
    elif selection == 1:
        user_stat()
    elif selection == 2:
        view_log()
    elif selection == 3:
        remove_user()
    elif selection == 4:
        admin_change_pass()
    else:
        print "Unrecognized command."
    if selection != 5:
        admin_menu()

    admin_menu()


def view_report():
    r = requests.get(HOST+"view_report")
    result = yaml.load(r.text)

    if result[0] == "400":
        logging.debug("Unsucessful retrieval of user list")
        print "Unsuccesful retrieval of user list"
    else:
        logging.debug("Succesfully retrieved user list")
        userlist = result[1]
        print "USERS:"
        for users in userlist:
            print users

def view_log():
    r = requests.get(HOST+"view_log")
    result = yaml.load(r.text)

    if result[0] == "400":
        logging.debug("Unsucessful retrieval of server log")
        print "Unsuccesful retrieval of server log"
    else:
        logging.debug("Succesfully retrieved server log")
        log = result[1]
        print "Recent Server Activity:"
        for activity in log:
            print activity

def runtime():
    print "Setup Complete: Intializing OneDir! Enjoy your day!"
    event_handler = FileSystemEventHandler()
    observer = Observer()
    #print WORKING_DIR

    #the recursive variable here determines whether the program watches subdirectories
    observer.schedule(event_handler, WORKING_DIR, recursive=True)
    observer.start()
    stop = threading.Event()
    th = Thread(target=job_processor, args=("Thread",stop))
    th.setDaemon(True)
    th.start()

    try:
        while True:
            synchronize()
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        stop.set()
    observer.join()
    th.join()

def init():
    if os.path.exists("./client_SAVEFILE"):
        global WORKING_DIR
        global SUID
        global TIME_STAMP
        global DIR_SNAPSHOT
        result = yaml.load(file('./client_SAVEFILE', 'r'))
        WORKING_DIR = result[0]
        SUID = result[1]
        TIME_STAMP = result[2]
        DIR_SNAPSHOT = result[3]
        runtime()

    else:
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
    logging.basicConfig(level=logging.DEBUG)
    #logging.basicConfig(filename='Client_Log.log',level=logging.DEBUG)
    # logging.basicConfig(filename='example.log',level=logging.DEBUG)
    init()