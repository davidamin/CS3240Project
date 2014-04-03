__author__ = 'User'
import sqlite3
import json
WORKING_DIR = '/Users/User/Documents/Github/CS3240Project'
db_connect = sqlite3.connect(WORKING_DIR + "/database.db")
with db_connect:
    cur = db_connect.cursor()
    cur.execute("SELECT username FROM users ", ())

    results = cur.fetchall()
    f = open('AdminReport', 'w')
    json.dump(results,f)
    print results