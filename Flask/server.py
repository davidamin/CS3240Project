from flask import *
import json
import os
import logging
import sqlite3
import uuid

import server_functions
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

@app.route('/signup/<username>/<passhash>')
def signup(username, passhash):
    db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
    with db_connect:
        cur = db_connect.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))

        results = cur.fetchall()
        for i in results:
            print results
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
                return json.dumps(("401","BAD"))

#Invoked will create a new directory with given username
#@app.route('/mkdir/<username>')
def mkdir(username):
    """Creates a directory in the user's server-side OneDir directory"""
    logging.debug("Making directory " + username + " in filestore" )
    full_filename = os.path.join(WORKING_DIR, username)
    if os.path.exists(full_filename):
        return username + " already exist!"
    else:
        os.mkdir(full_filename)
        return "A file has been made for user " + username

#upload file into user account
@app.route('/upload-file/<sessionhash>/<path:filename>', methods=['GET', 'POST'])
def upload_file(sessionhash,filename):
    if request.method == 'POST':
        logging.debug("New File: " + filename + " .... Processing")

        user = authenticate(sessionhash)
        if (user[0]):
            file = request.files['file']
            userpath = os.path.join(WORKING_DIR,"filestore",user[1])
            file.save(os.path.join(userpath, filename))
            logging.info("File: " + os.path.join(userpath, filename) + " ... Created")
            return json.dumps(("200", "OK"))
        else:
            return json.dumps(("400", "BAD"))

#upload file into user account
@app.route('/new-dir/<sessionhash>/<path:filepath>', methods=['GET', 'POST'])
def new_dir(sessionhash,filepath):
    logging.debug("New Directory: " + filepath + " .... Processing")
    user = authenticate(sessionhash)
    if (user[0]):
        userpath = os.path.join(WORKING_DIR,"filestore",user[1])
        #file.save(os.path.join(userpath, filename))
        if not os.path.exists(userpath+"/"+filepath):
            os.makedirs(userpath+"/"+filepath)
            logging.info("New Directory: " + filepath + " Created for user: " + user[1])
        return json.dumps(("200", "OK"))
    else:
        return json.dumps(("400", "BAD"))

@app.route('/delete-file/<sessionhash>/<path:file>')
def delete_file(sessionhash,file):
    user = authenticate(sessionhash)
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
        logging.error("User does not exist")
        return json.dumps(("400"), "BAD")

@app.route('/delete-dir/<sessionhash>/<path:filepath>')
def delete_dir(sessionhash,filepath):
    user = authenticate(sessionhash)
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
        logging.error("User does not exist")
        return json.dumps(("400"), "BAD")

# #use this to send a file from user
# @app.route('/send/<filename>', methods=['GET','POST'])
# def send(filename):
#     userpath = os.path.join(WORKING_DIR,filename)
#     return send_file(userpath, as_attachment=True)

@app.route('/view_files/<username>')
def view_files(username):
    """Returns the size and number of files stored in a directory on the server"""
    onlyfiles = []
    full_filename = os.path.join(WORKING_DIR, username)
    for f in os.listdir(full_filename):
        onlyfiles.append(f)
        logging.debug(onlyfiles)
    return "Here are the files of the user " + username + ": " + onlyfiles.__str__()


# Invoked when you access: http://127.0.0.1:5000/get-file-data/somedata.txt
@app.route('/get-file-data/<filename>')
def get_file_data(filename):
    logging.debug("entering get_file_data")
    full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
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



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(filename='example.log',level=logging.DEBUG)
    logging.info("Starting server")
    app.run(debug = True)