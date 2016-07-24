from flask import jsonify, Response, json, request, session, redirect, url_for, escape, send_file, render_template
from functools import wraps
import requests

from OpenAgua import app

from connection import *
from conversions import *

# the following setup should be done via the user interface and user management system

url = app.config['URL']
hydra_username = app.config['HYDRA_USERNAME']
hydra_password = app.config['HYDRA_PASSWORD']

conn = connection(url = url)
conn.login(username = hydra_username, password = hydra_password)
session_id = conn.session_id
user = conn.call('get_user_by_name', {'username':hydra_username})
projects = conn.call('get_projects',{'user_id':user.id})
project_name = 'Monterrey'
network_name = 'base_network'

# Set up project. To be deleted once we can integrate into the UI.

# load / create project
try:
    project = get_project_by_name(conn, project_name)
except: # project doesn't exist, so let's create it
    proj = dict(name = project_name)
    project = conn.call('add_project', {'project':proj})  

# load / create network
exists = conn.call('network_exists', {'project_id':project.id, 'network_name':network_name})
if exists=='Y':
    network = get_network_by_name(conn, project_name, network_name)
else:
    net = dict(
        project_id = project.id,
        name = network_name,
        description = 'Prototype DSS network for Monterrey'
    )
    network = conn.call('add_network', {'net':net})
activated = conn.call('activate_network', {'network_id':network.id})


app.secret_key = app.config['SECRET_KEY']

username = app.config['USERNAME']
password = app.config['PASSWORD']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return decorated_function

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
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html',
                           username=username,
                           projects=projects)

@app.route('/network_editor')
@login_required
def network_editor():
    return render_template('network_editor.html',
                           username=username,
                           session_id=session_id,
                           project_name=project_name,
                           network_name=network_name)



@app.route('/_load_network')
def load_network():
    network = get_network_by_name(conn, project_name, network_name)
    features = get_features(network)

    status_code = 1
    status_message = 'Network "%s" loaded' % network_name

    features = json.dumps(features)
    result = dict( status_code = status_code, status_message = status_message, features = features )
    result_json = jsonify(result=result)
    return result_json

@app.route('/_save_network')
def save_network():

    network = get_network_by_name(conn, project_name, network_name)
    features = get_features(network)

    new_features = request.args.get('new_features')
    new_features = json.loads(new_features)['shapes']        

    if new_features:
        add_features(conn, network.id, new_features)
        network = get_network(conn, network.id) # get updated network
        features = get_features(network) # get updated features
        status_code = 1
        status_message = 'Edits saved!'
    else:
        status_code = 2
        status_message = 'No edits detected'

    # get updated network and features

    features = json.dumps(features)
    result = dict(
        status_code = status_code,
        status_message = status_message,
        features = features
    )

    result_json = jsonify(result=result)
    return result_json