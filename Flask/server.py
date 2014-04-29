from flask import *
import json
import os
import logging
import sqlite3
import uuid
import shutil
import pickle
from watchdog.utils import dirsnapshot
from datetime import datetime

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif'])
app.config.update(dict(
    DATABASE='database.db',
    USERS= {}))

#WORKING_DIR = '/Users/User/Documents/Github/CS3240Project'
#WORKING_DIR = '/home/david/WindowsFolder/Documents/GitHub/CS3240Project'
#WORKING_DIR = '/Users/Marbo/PycharmProjects/CS3240Project/Flask'
#WORKING_DIR = '/Users/brian/Public/CS3240Project/Flask'

def authenticate(sessionhash):
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("SELECT username FROM sessions WHERE session = ?", (sessionhash,))
        results = cur.fetchall()
        if len(results) == 0:
            logging.debug("No session hash matched...")
            return (False, "")
        else:
            stored_username = results.pop()
            return (True, stored_username[0])

def is_Admin(sessionhash):
    valid_sess = authenticate(sessionhash)
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    if(valid_sess[0]):
        with db_connect:
            cur = db_connect.cursor()
            cur.execute("SELECT user_role FROM users WHERE username = ?", (valid_sess[1],))
            results = cur.fetchone()
            if results[0] == 1:
                return True
            else:
                return False
    else:
        return False

def allowed_file(filename):
    pathandname, extens = os.path.splitext(filename)
    if extens in ALLOWED_EXTENSIONS or len(extens) == 0:
        return True
    else:
        return False

@app.route('/signup/<username>/<passhash>')
def signup(username, passhash):
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))

        results = cur.fetchall()
        if len(results) == 0:
            logging.debug("No user named : " + username + " found... Creating...")
            cur.execute("INSERT INTO users (username, passhash, user_role) VALUES (?, ?, ?)", (username, passhash, 0))
            mkdir(username)
            mkdir(os.path.join(username,"shared"))
            snapshot = pickle.dumps(dirsnapshot.DirectorySnapshot(os.path.join(WORKING_DIR,'filestore',username)))

            date = str(datetime.now())
            #cur.execute("DELETE FROM snaps WHERE username = ?", (user[1],))
            cur.execute("INSERT INTO snaps (username, time_stamp, snapshot) VALUES (?, ?, ?)", (username,date, snapshot))

            return json.dumps(("200", date))

        else:
            logging.debug("User named : " + username + " found. Aborting Signup")
            return json.dumps(("404", "BAD"))


@app.route('/signin/<username>/<passhash>')
def signin(username, passhash):
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("SELECT passhash FROM users WHERE username = ?", (username,))

        results = cur.fetchall()
        if len(results) == 0:
            logging.debug("No user named : " + username + " found...")
            return json.dumps(("404","BAD"))
        else:
            logging.debug("User named : " + username + " found.")
            stored_hash = results.pop()
            CURRENT_USER = username
            print(CURRENT_USER)
            if stored_hash[0] == passhash:
                logging.debug("User named : " + username + " Authenticated")
                session_id = uuid.uuid4().hex
                temp_date = datetime.now()


                cur.execute("INSERT INTO sessions (username, session, date) VALUES (?, ?, ?)", (username, session_id, temp_date.strftime('%Y/%m/%d %H:%M:%S')))
                return json.dumps(("200",session_id))
            else:
                logging.debug("User named : " + username + " Was not Authenticated")
                return json.dumps(("401","BAD"))

@app.route('/changepass/<username>/<passhash>/<sessionhash>')
def changepass(username, passhash, sessionhash):
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        if(is_Admin(sessionhash)):
            cur.execute("UPDATE users SET passhash = ? WHERE username = ?", (passhash, username))
            print "ADMIN CHANGING PASSWORD FOR USER " + username
            return json.dumps(("200",))
        authres = authenticate(sessionhash)

        if(authres[0]):
            print authres[1]
            curuser = authres[1]
            if(username == curuser):
                cur.execute("UPDATE users SET passhash = ? WHERE username = ?", (passhash, curuser))
                logging.debug("User named : " + username + " found.")
                return json.dumps(("200",))
            else:
                logging.debug("User tried to change someone else's password")
                return json.dumps(("404","BAD"))
        else:
            logging.debug("Invalid user trying to make a password change")
            return json.dumps(("404","BAD"))

#Invoked will create a new directory with given username
#@app.route('/mkdir/<username>')
def mkdir(username):
    """Creates a directory in the user's server-side OneDir directory"""
    logging.debug("Making directory " + username + " in filestore" )
    full_filename = os.path.join(WORKING_DIR,'filestore', username)
    if os.path.exists(full_filename):
        return username + " already exist!"
    else:
        os.mkdir(full_filename)
        return "A file has been made for user " + username

@app.route('/snapshot/<sessionhash>')
def snapshot(sessionhash):
    user = authenticate(sessionhash)
    logging.debug("User : " + user[1] + "Snapshot Save.... Processing")

    if (user[0]):
        #data = pickle.loads(request.data)
        snapshot = dirsnapshot.DirectorySnapshot(os.path.join(WORKING_DIR, 'filestore',user[1]),recursive=True)
        db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
        with db_connect:
            cur = db_connect.cursor()
            date = str(datetime.now())
            #cur.execute("DELETE FROM snaps WHERE username = ?", (user[1],))
            cur.execute("INSERT INTO snaps (username, time_stamp, snapshot) VALUES (?, ?, ?)", (user[1],date, pickle.dumps(snapshot)))

        logging.info("User :  " + user[1] + " Updated Snapshot with time_stamp : " + date)
        return json.dumps(("200", date))
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400", "BAD"))


@app.route('/get-snapshot/<sessionhash>', methods=['GET', 'POST'])
def get_snapshot(sessionhash):
    if request.method == 'POST':
        user = authenticate(sessionhash)
        logging.debug("User : " + user[1] + "Snapshot Access.... Processing")

        if (user[0]):
            db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
            timestamp = request.data
            with db_connect:
                cur = db_connect.cursor()
                if timestamp == "new":
                    cur.execute("SELECT snapshot FROM snaps WHERE username = ? ORDER BY time_stamp ASC", (user[1],))
                else:
                    cur.execute("SELECT snapshot FROM snaps WHERE username = ? AND time_stamp = ?", (user[1],timestamp))
                res = cur.fetchone()
                ref_snapshot = pickle.loads(res[0])

                cur.execute("SELECT time_stamp FROM snaps WHERE username = ? ORDER BY time_stamp DESC", (user[1],))
                res = cur.fetchone()

                serv_snapshot = dirsnapshot.DirectorySnapshot(os.path.join(WORKING_DIR, 'filestore',user[1]),recursive=True)

                diff = dirsnapshot.DirectorySnapshotDiff(ref_snapshot,serv_snapshot)
                logging.info("User :  " + user[1] + " Downloaded Snapshot")
                return json.dumps(("200", os.path.join(WORKING_DIR,'filestore',user[1]), pickle.dumps(diff), res[0]))
        else:
            logging.error("User named : " + user[1] + " Was not Authenticated")
            return json.dumps(("400", "BAD"))


@app.route('/timestamp/<sessionhash>')
def timestamp(sessionhash):
    user = authenticate(sessionhash)
    if (user[0]):
        db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
        with db_connect:
            cur = db_connect.cursor()
            cur.execute("SELECT time_stamp FROM snaps WHERE username = ? ORDER BY time_stamp DESC", (user[1],))

            ret = cur.fetchone()
            if len(ret) == 0:
                logging.info("User: " + user[1] + " Does not have a Timestamp")
                return json.dumps(("401", "NONE"))
            else:
                logging.info("User :  " + user[1] + " Accessed Timestamp ")
                return json.dumps(("200", ret[0]))
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400", "BAD"))

#upload file into user account
@app.route('/upload-file/<sessionhash>/<path:filename>', methods=['GET', 'POST'])
def upload_file(sessionhash,filename):
    if request.method == 'POST':

        user = authenticate(sessionhash)
        logging.debug("User : " + user[1] + "New File : " + filename + " .... Processing")

        if not(allowed_file(filename)):
            logging.debug("Invalid File Type error encountered on " + filename)
            return json.dumps(("400"), "BAD")

        if (user[0]):
            file = request.files['file']
            userpath = os.path.join(WORKING_DIR,"filestore",user[1])
            file.save(os.path.join(userpath, filename))
            logging.info("File: " + os.path.join(userpath, filename) + " ... Created")
            return json.dumps(("200", "OK"))
        else:
            logging.error("User named : " + user[1] + " Was not Authenticated")
            return json.dumps(("400", "BAD"))

#upload file into user account
@app.route('/new-dir/<sessionhash>/<path:filepath>', methods=['GET', 'POST'])
def new_dir(sessionhash,filepath):
    user = authenticate(sessionhash)
    logging.debug("User : " + user[1] + "New Directory : " + filepath + " .... Processing")

    if (user[0]):
        userpath = os.path.join(WORKING_DIR,"filestore",user[1])
        #file.save(os.path.join(userpath, filename))
        if not os.path.exists(userpath+"/"+filepath):
            os.makedirs(userpath+"/"+filepath)
            logging.info("New Directory: " + filepath + " ... Created")
        return json.dumps(("200", "OK"))
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400", "BAD"))

@app.route('/delete-file/<sessionhash>/<path:file>')
def delete_file(sessionhash,file):
    user = authenticate(sessionhash)
    logging.debug("User : " + user[1] + "Delete File : " + file + " .... Processing")
    if (user[0]):
        #filename = secure_filename(file)
        userpath = os.path.join(WORKING_DIR,"filestore",user[1],file)
        if os.path.exists(userpath):
            logging.debug("File: " + userpath + " Exists... Deleting")
            os.remove(userpath)
            return json.dumps(("200", "OK"))
        else:
            logging.debug("File: " + userpath + " Does not Exist.... Nothing to Delete")
            return json.dumps(("201", "OK"))
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400"), "BAD")

@app.route('/delete-dir/<sessionhash>/<path:filepath>')
def delete_dir(sessionhash,filepath):
    user = authenticate(sessionhash)
    logging.debug("User : " + user[1] + "Delete Directory : " + filepath + " .... Processing")
    if (user[0]):
        userpath = os.path.join(WORKING_DIR,"filestore",user[1],filepath)
        if os.path.exists(userpath):
            logging.debug("File: " + userpath + " Exists... Deleting")
            shutil.rmtree(userpath)
            return json.dumps(("200", "OK"))
        else:
            logging.debug("Dir: " + userpath + " Does not Exist.... Nothing to Delete")
            return json.dumps(("201", "OK"))
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400"), "BAD")




@app.route('/download-file/<sessionhash>/<path:filepath>')
def download_file(sessionhash, filepath):
    user = authenticate(sessionhash)
    logging.debug("User : " + user[1] + "downloading file : " + filepath + " .... Processing")

    if (user[0]):
        # print os.path.join("filestore", user[1], filepath)
        return send_file(os.path.join(WORKING_DIR, "filestore", user[1], filepath),as_attachment=True)
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400"), "BAD")

@app.route('/download-link/<username>/<path:filepath>')
def download_link(username, filepath):
    #print os.path.join(WORKING_DIR, "filestore" , username, "shared", filepath)

    if (os.path.exists(os.path.join(WORKING_DIR, "filestore" , username, "shared", filepath))):
        # print os.path.join("filestore", user[1], filepath)
        return send_file(os.path.join(WORKING_DIR, "filestore" , username, "shared", filepath), as_attachment=True)
    else:
        logging.error("Path to file was invalid")
        logging.error(os.path.join(WORKING_DIR, "filestore", filepath))
        return json.dumps(("400"), "BAD")

@app.route('/is-dir/<sessionhash>/<path:filepath>')
def is_dir(sessionhash, filepath):
    user = authenticate(sessionhash)

    logging.debug("User : " + user[1] + "checking if directory : " + filepath + " .... Processing")

    if (user[0]):
        # print os.path.join("filestore", user[1], filepath)
        return json.dumps(("200", os.path.isdir(os.path.join(WORKING_DIR, "filestore", user[1],filepath))))
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400"), "BAD")


def recursealldir(path, filename):
    # in_filename = os.path.join(path,filename.__str__())
    # directory = {}
    # print in_filename
    # # if has more than 1 link then it must be a dir
    # print os.stat(in_filename).st_nlink
    # if not os.path.isdir(in_filename):
    #     directory[filename.__str__()] = os.path.getsize(in_filename)
    #     print "NO NEWSTR"
    #     return directory.__str__()
    # else :
    #     subdirectory ={}
    #     #this means that there are more than one file in path so we go through each
    #     for infile in os.listdir(in_filename):
    #         in_filename2 = os.path.join(in_filename,infile.__str__())
    #         #recursively checks if inside is also a dir
    #         #not another path
    #         if ((os.stat(in_filename2).st_nlink) < 2):
    #             #base case:not a directory so add normal to subdirectory
    #             subdirectory[infile.__str__()] = os.path.getsize(in_filename2)
    #
    #         else:
    #             #it is a directory so makes another dictonary for it
    #             subdirectory[infile.__str__()] = recursealldir(in_filename,infile.__str__())
    #     oldstr = subdirectory.__str__()
    #     newstr = oldstr.replace("\\", "")
    # print "NEWSTR: " + newstr
    # return newstr

    top = os.path.join(path, filename)
    size = 0
    dir_size = 0
    file_size = 0

    for root, dirs, files in os.walk(top):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        dir_size += len(dirs)
        file_size += len(files)

    return (size, dir_size, file_size)
                #return subdirectory to add to files

@app.route('/stat/<username>')
def stat(username):

    """Returns the size and number of files stored in a directory on the server"""
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        results = cur.fetchall()
        if len(results) == 0:
            logging.debug("No user named : " + username + " found...")
            return json.dumps(("400","User does not exist"))
        else:
            # files = {}
            full_filename = os.path.join(WORKING_DIR, "filestore", username)
            ans = recursealldir(os.path.join(WORKING_DIR, "filestore"), username)
            foldercount = ans[1]
            filescount = ans[2]
            totalsize = ans[0]
            result = "User: " +username + " [ Folder count: " + str(foldercount) \
                   + " , File count:" + str(filescount) + ", Total size: "+ str(totalsize) + "]"

            return json.dumps(("200",result))

@app.route('/userstat')
def userstat():
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    stat_list = []
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("SELECT username FROM users ", ())
        user_list = []
        results = cur.fetchall()
        for uniresults in results:
            unistr = uniresults[0]
            user_list.append(unistr.encode('ascii','ignore'))
        for s in user_list:
            if ( s != "admin"):
                full_filename = os.path.join(WORKING_DIR, "filestore", s)
                ans = recursealldir(os.path.join(WORKING_DIR, "filestore"), s)
                foldercount = ans[1]
                filescount = ans[2]
                totalsize = ans[0]
                result = "Username: " +s + " [ Folder count: " + str(foldercount) \
                       + " , File count: " + str(filescount) + ", Total size: "+ str(totalsize) + "]"
                print result
                stat_list.append(result)

    return json.dumps(("200",stat_list))

@app.route('/remove_user/<username>/<delfiles>')
def remove_user(username, delfiles):
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("DELETE FROM users WHERE username = ?", (username,))
        if(delfiles == 1):
            userpath = os.path.join(WORKING_DIR,"filestore",username)
            if os.path.exists(userpath):
                logging.debug("File: " + userpath + " Exists... Deleting")
                shutil.rmtree(userpath)
            else:
                logging.debug("Dir: " + userpath + " Does not Exist.... Nothing to Delete")
        return json.dumps(("200","User" + username + " removed."))

# Invoked when you access: http://127.0.0.1:5000/get-file-data/somedata.txt
@app.route('/get-file-data/<filename>')
def get_file_data(filename):
    logging.debug("entering get_file_data")
    full_filename = os.path.join(WORKING_DIR, filename)
    if not os.path.exists(full_filename):
        logging.warn("file does not exist on server: " + full_filename)
        ret_value = { "result" : -1, "msg" : "file does not exist"}
    else:
        with open(full_filename, "rb") as in_file:
            snippet = in_file.read()
        file_size = os.path.getsize(full_filename)
        ret_value = { "result" : 0, "size" : file_size, "value" : snippet}
    return json.dumps(ret_value)

@app.route('/view_report')
def view_report():
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("SELECT username FROM users ", ())
        user_list = []
        results = cur.fetchall()
        for uniresults in results:
            unistr = uniresults[0]
            user_list.append(unistr.encode('ascii','ignore'))
    return json.dumps(("200", user_list))

@app.route('/view_log')
def view_log():
    logFile = open("server.log", 'r')
    commandList = []
    for line in logFile:
        commandList.append(line)
    return json.dumps(("200", commandList))

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(filename='server.log',level=logging.DEBUG)
    logging.info("Starting server")
    print "Enter Base of Server Folder: (Should be the Flask Folder): "
    print "Example: /Users/brian/Public/CS3240Project/Flask"
    global WORKING_DIR
    WORKING_DIR = raw_input("Absolute Folder Path: ")
    print WORKING_DIR
    app.run(debug = True, host='0.0.0.0')
