__author__ = 'User'
from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    #return "Hello, World!"
    user = { 'nickname': 'David' } # fake user
    return render_template("index.html",user = user)