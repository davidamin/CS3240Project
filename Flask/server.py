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
#WORKING_DIR = '/Users/brian/Public/CS3240Project/Flask'
WORKING_DIR = '/Users/Marbo/PycharmProjects/CS3240Project/Flask'
CURRENT_USER=''


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
            cur.execute("INSERT INTO users (username, passhash) VALUES (?, ?)", (username, passhash))
            mkdir(username)
            return "User Account Successfully Created!"
        else:
            logging.debug("User named : " + username + " found. Aborting Signup")
            return "User Account Already Exists!"


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
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print(CURRENT_USER + "user")
        file = request.files['file']
        filename = secure_filename(file.filename)
        userpath = os.path.join(WORKING_DIR,CURRENT_USER)
        print(userpath)
        file.save(os.path.join(userpath, filename))
        return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
#use this to send a file from user
@app.route('/send', methods=['GET','POST'])
def index():
    userpath = '/Users/Marbo/PycharmProjects/CS3240Project/Flask/testing.txt'
    return send_file(userpath, as_attachment=True)
# Need to figure out how to add file
#Invoked will go directory with given username and add file
@app.route('/user-add-file/<username>/<filename>')
def user_add_file(username, filename):
    """Creates a directory in the user's server-side OneDir directory"""
    full_filename = os.path.join(WORKING_DIR, 'filestore', username)
    if os.path.exists(full_filename):
        file_add =os.path.join(full_filename,filename)

        return username + " exist! Adding file: " + filename + " to user directory"

    else:
        return "This user does not exist you cannot add file"
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

# Invoked when you access: http://127.0.0.1:5000/replace-file-data/newdata.txt/data   (makes changes to file:newdata.txt by putting info in data
@app.route('/replace-file-data/<filename>/<data>')
def replace_data( filename, data):
    full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
    logging.debug("Replacing file data")
    with open( full_filename, "w") as f:
        f.write(data)
    return "server wrote data to: " + filename


#Invoked when you access: http://127.0.0.1:5000/append-data-file/newdata.txt/data  to append data into existing files
@app.route('/append-data-file/<filename>/<data>')
def append_file( filename, data):
    full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
    with open( full_filename, "a") as f:
        f.write(data)
    return "server appended data to: " + filename

#Invoked when you access: http://127.0.0.1:5000/delete-file/newdata.txt to delete newdata.txt file
# only allows deletion of file but not directories
@app.route('/delete-file/<filename>')
def delete_file( filename):
    full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
    os.remove(full_filename)

    return "file deleted: " + filename

#Invoked when you access: http://127.0.0.1:5000/delete-file/newdata.txt to delete newdata.txt file
@app.route('/rename-file/<filename>/<newfilename>')
def rename_file( filename , newfilename):
    full_filename = os.path.join(WORKING_DIR, 'filestore', filename)
    new_filename = os.path.join(WORKING_DIR, 'filestore', newfilename)
    os.rename(full_filename, new_filename)

    return "file renamed: " + filename +" to " + newfilename



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(filename='example.log',level=logging.DEBUG)
    logging.info("Starting server")
    app.run(debug = True)