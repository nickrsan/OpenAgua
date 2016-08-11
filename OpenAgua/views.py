from __future__ import print_function
from flask import jsonify, Response, json, request, session, redirect, url_for, escape, send_file, render_template, flash
from werkzeug.utils import secure_filename
import requests
import sys

from OpenAgua import app

from .connection import connection
from .conversions import *

app.secret_key = app.config['SECRET_KEY']

# this needs to be done properly through a user management system
username = app.config['USERNAME']
password = app.config['PASSWORD']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != username or request.form['password'] != password:
            error = 'Invalid Credentials. Please try again.'
        else:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('user_home.home'))
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/overview')
@login_required
def overview():    
    return render_template('overview.html') 

@app.route('/template')
@login_required
def template():    
    return render_template('template.html')


