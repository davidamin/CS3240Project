from flask import *
import json
import os
import logging
import sqlite3
import uuid
import pickle


import time
from datetime import datetime
from werkzeug.utils import secure_filename
"""
Demo of server using Flask.  Can be used by either:
a) typing URLs into a webbrowser's address box, or
b) by a client sending it HTTP requests. A sample client is provided, requests_client1.py.

3rd party libraries to be installed:
a) Flask

Note: PyCharm allows you to create a new project for Flask.  This was created using that. Try it.

This program also shows how to use logging in Python. Logging libraries are used in real software
to provide informational messages.  Especially for servers.  See this link for more info:
http://docs.python.org/2/howto/logging.html#logging-basic-tutorial

Important: this command:   http://127.0.0.1:5000/get-file-data/somedata.txt
requires that there be a subdirectory called 'filestore' in the folder given by the
variable WORKING_DIR defined below.  This command will look for a file called
'somedata.txt' in that folder. So to see this work, you must adjust WORKING_DIR,
create the subdirectory, and put a file or files in there.

"""

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config.update(dict(
    DATABASE='database.db',
    USERS= {}))

WORKING_DIR = '/Users/brian/Public/CS3240Project/Flask'
#WORKING_DIR = '/Users/Marbo/PycharmProjects/CS3240Project/Flask'


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
            results = cur.fetchall()
            if results[0][0] == 1:
                return True
            else:
                return False
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
            return json.dumps(("200", "GOOD"))
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
            return json.dumps(("200","Successfully changed password"))
        authres = authenticate(sessionhash)

        if(authres[0]):
            curuser = authres[1]
            if(username == curuser):
                cur.execute("UPDATE users SET passhash = ? WHERE username = ?", (passhash, curuser))
                logging.debug("User named : " + username + " found.")
                return json.dumps(("200","Successfully changed password"))
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
    full_filename = os.path.join(WORKING_DIR,"filestore", username)
    if os.path.exists(full_filename):
        return username + " already exist!"
    else:
        os.mkdir(full_filename)
        return "A file has been made for user " + username

#upload file into user account
@app.route('/upload-file/<sessionhash>/<path:filename>', methods=['GET', 'POST'])
def upload_file(sessionhash,filename):
    if request.method == 'POST':

        user = authenticate(sessionhash)
        logging.debug("User : " + user[1] + "New File : " + filename + " .... Processing")

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
            os.removedirs(userpath)
            return json.dumps(("200", "OK"))
        else:
            logging.debug("Dir: " + userpath + " Does not Exist.... Nothing to Delete")
            return json.dumps(("201", "OK"))
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400"), "BAD")

@app.route('/snapshot/<sessionhash>', methods=['GET', 'POST'])
def snapshot(sessionhash):
    if request.method == 'POST':

        user = authenticate(sessionhash)
        logging.debug("User : " + user[1] + "Snapshot Save.... Processing")

        if (user[0]):
            #data = pickle.loads(request.data)
            db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
            with db_connect:
                cur = db_connect.cursor()
                date = str(datetime.now())
                cur.execute("DELETE FROM snaps WHERE username = ?", (user[1],))
                cur.execute("INSERT INTO snaps (username, time_stamp, snapshot) VALUES (?, ?, ?)", (user[1],date, request.data))

            logging.info("User :  " + user[1] + " Updated Snapshot with time_stamp : " + date)
            return json.dumps(("200", date))
        else:
            logging.error("User named : " + user[1] + " Was not Authenticated")
            return json.dumps(("400", "BAD"))

    else:
        print request.method

@app.route('/timestamp/<sessionhash>')
def timestamp(sessionhash):
    user = authenticate(sessionhash)
    if (user[0]):
        db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
        with db_connect:
            cur = db_connect.cursor()
            cur.execute("SELECT time_stamp FROM snaps WHERE username = ?", (user[1],))

            ret = cur.fetchone()
            logging.info("User :  " + user[1] + " Accessed Timestamp ")
            return json.dumps(("200"), ret[0])
    else:
        logging.error("User named : " + user[1] + " Was not Authenticated")
        return json.dumps(("400", "BAD"))


# #use this to send a file from user
# @app.route('/send/<filename>', methods=['GET','POST'])
# def send(filename):
#     userpath = os.path.join(WORKING_DIR,filename)
#     return send_file(userpath, as_attachment=True)


def recursealldir(path, filename):
    in_filename = os.path.join(path,filename.__str__())
    directory = {}
    # if has more than 1 link then it must be a dir
    if (os.stat(in_filename).st_nlink) < 2:
        directory[filename.__str__()] = filename.__sizeof__()
        return directory.__str__()
    else :
        subdirectory ={}
        #this means that there are more than one file in path so we go through each
        for infile in os.listdir(in_filename):
            in_filename2 = os.path.join(in_filename,infile.__str__())
            #recursively checks if inside is also a dir
            #not another path
            if ((os.stat(in_filename2).st_nlink) < 2):
                #base case:not a directory so add normal to subdirectory
                subdirectory[infile.__str__()] = infile.__sizeof__()

            else:
                #it is a directory so makes another dictonary for it
                subdirectory[infile.__str__()] = recursealldir(in_filename,infile.__str__())
        oldstr = subdirectory.__str__()
        newstr = oldstr.replace("\\", "")

    return newstr
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
            files = {}
            full_filename = os.path.join(WORKING_DIR, username)
            count = 0
            memory = 0
            for f in os.listdir(full_filename):
                files[f.__str__()]= f.__sizeof__()

                logging.debug(files)
                count = count + 1
                memory =memory + f.__sizeof__()
            return json.dumps(("200","" + username + " has " + count.__str__()  + " files with total memory of "+ memory.__str__() + ": " + files.__str__() + ""))

@app.route('/remove_user/<username>/<delfiles>')
def remove_user(username, delfiles):
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("DELETE FROM users WHERE username = ?", (username,))
        if(delfiles):
            userpath = os.path.join(WORKING_DIR,"filestore",username)
            print userpath
            if os.path.exists(userpath):
                logging.debug("File: " + userpath + " Exists... Deleting")
                os.removedirs(userpath)
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


# # Invoked when you access: http://127.0.0.1:5000/replace-file-data/newdata.txt/data   (makes changes to file:newdata.txt by putting info in data
# @app.route('/replace-file-data/<filename>/<data>')
# def replace_data( filename, data):
#     full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
#     logging.debug("Replacing file data")
#     with open( full_filename, "w") as f:
#         f.write(data)
#     return "server wrote data to: " + filename
#
#
# #Invoked when you access: http://127.0.0.1:5000/append-data-file/newdata.txt/data  to append data into existing files
# @app.route('/append-data-file/<filename>/<data>')
# def append_file( filename, data):
#     full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
#     with open( full_filename, "a") as f:
#         f.write(data)
#     return "server appended data to: " + filename

#Invoked when you access: http://127.0.0.1:5000/delete-file/newdata.txt to delete newdata.txt file
# only allows deletion of file but not directories


# #Invoked when you access: http://127.0.0.1:5000/delete-file/newdata.txt to delete newdata.txt file
# @app.route('/rename-file/<filename>/<newfilename>')
# def rename_file( filename , newfilename):
#     full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
#     new_filename = os.path.join(WORKING_DIR, 'filestore', newfilename)
#     os.rename(full_filename, new_filename)
#
#     return "file renamed: " + filename +" to " + newfilename

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
        #f = open('AdminReport', 'w')
        #json.dump(results,f)
    # result_html = '''
    # <!doctype html>
    # <title>Users</title>
    # <h1>User List</h1>
    # <body>
    # '''
    # for formatted_result in user_list:
    #     result_html += formatted_result
    #     result_html += "<br>"
    #
    # result_html += "</body>"
    # return result_html
    return json.dumps(("200", user_list))

@app.route('/view_log')
def view_log():
    logFile = open("server.log", 'r')
    commandList = []
    for line in logFile:
        commandList.append(line)
    return json.dumps(("200", commandList))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #logging.basicConfig(filename='server.log',level=logging.DEBUG)
    logging.info("Starting server")
    app.run(debug = True)
