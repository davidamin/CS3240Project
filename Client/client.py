from passlib.hash import md5_crypt
import logging
import requests



HOST = 'http://127.0.0.1:5000/'



def new_user():
    print "Creating new account. Please fill out the following details:"
    username = raw_input('Username: ')
    password = raw_input('Password: ')
    confirm = raw_input('Confirm Password: ')

    if password == confirm :
        r = requests.get(HOST + "signup/" + username + "/" + password)
        print r.text




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(filename='example.log',level=logging.DEBUG)
    new_user()