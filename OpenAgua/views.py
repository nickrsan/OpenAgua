from __future__ import print_function
from flask import jsonify, Response, json, request, session, redirect, url_for, escape, send_file, render_template, flash
from flask_user import login_required
from flask.ext.login import current_user
import requests
import sys

from OpenAgua import app

from .connection import connection

app.secret_key = app.config['SECRET_KEY']

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('user_home.home'))
    else:
        return render_template('index.html')
    
@app.route('/after_registration')
def after_registration():
    return render_template('after_registration.html')

@app.route('/template')
@login_required
def template():    
    return render_template('template.html')


