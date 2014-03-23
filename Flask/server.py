from flask import *
import json
import os
import logging
import sqlite3
import server_functions
import time
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

app.config.update(dict(
    DATABASE='database.db',
    USERS= {}))
WORKING_DIR = '/Users/Marbo/PycharmProjects/Flask/'

'''
@app.route('/login', methods=['POST', 'GET'])
def login():
    username = request.form['username']
    password = request.form['password']
    #hold check if server has the user '''

#Invoked will create a new directory with given username
@app.route('/mkdir/<username>')
def mkdir(username):
    """Creates a directory in the user's server-side OneDir directory"""
    logging.debug("Making directory " + username + " in filestore" )
    full_filename = os.path.join(WORKING_DIR, 'filestore', username)
    if os.path.exists(full_filename):
        return username + " already exist!"
    else:
        os.mkdir(full_filename)
        return "A file has been made for user " + username

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
    full_filename = os.path.join(WORKING_DIR, 'filestore', username)
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