from flask import jsonify, Response, json, request, session, redirect, url_for, escape, send_file, render_template
from flask import Markup
from functools import wraps
import requests

from OpenAgua import app

from connection import connection
from conversions import *

url = app.config['HYDRA_URL']
hydra_username = app.config['HYDRA_USERNAME']
hydra_password = app.config['HYDRA_PASSWORD']

app.secret_key = app.config['SECRET_KEY']

# this needs to be done properly through a user management system
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

    # FUTURE: for all of this, add post methods or auto-load from user settings
        
    # connect
    conn = connection(url=url)
    conn.login(username = hydra_username, password = hydra_password)
    session['session_id'] = conn.session_id
    session['user_id'] = conn.get_user_by_name(hydra_username)
    
    # load / create project
    session['project_name'] = app.config['HYDRA_PROJECT_NAME']
    try:
        project = conn.get_project_by_name(session['project_name'])
    except:
        proj = dict(name = session['project_name'])
        project = conn.add_project(proj)
    session['project_id'] = project.id
    project_id = session['project_id']

    # load / create / activate network
    session['network_name'] = app.config['HYDRA_NETWORK_NAME']
    exists = conn.call('network_exists', {'project_id':project_id, 'network_name':session['network_name']})
    if exists=='Y':
        network = conn.get_network_by_name(project_id, session['network_name'])
    else:
        net = dict(
            project_id = project_id,
            name = session['network_name'],
            description = 'Prototype DSS network for Monterrey'
        )
        network = conn.call('add_network', {'net':net})
    session['network_id'] = network.id
    activated = conn.call('activate_network', {'network_id':session['network_id']})

    return render_template('home.html',
                           username = username,
                           project_name = session['project_name'],
                           network_name = session['network_name'])

@app.route('/network_editor')
@login_required
def network_editor():   
    
    popup_html_node = '<form>it\'s a node!<input type="text"name="lastname"></form>'
    
    popup_html_link = 'test'
    
    return render_template('network_editor.html',
                           username=username,
                           session_id=session['session_id'],
                           project_name=session['project_name'],
                           network_name=session['network_name'],
                           popup_html_node=Markup(popup_html_node),
                           popup_html_link=Markup(popup_html_link))    

@app.route('/_load_network')
def load_network():
    conn = connection(url=url, session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    features = get_features(network)

    status_code = 1
    status_message = 'Network "%s" loaded' % session['network_name']

    features = json.dumps(features)
    result = dict( status_code = status_code, status_message = status_message, features = features )
    result_json = jsonify(result=result)
    return result_json

@app.route('/_save_network')
def save_network():
    conn = connection(url=url, session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    features = get_features(network)

    new_features = request.args.get('new_features')
    new_features = json.loads(new_features)['shapes']        

    if new_features:
        add_features(conn, session['network_id'], new_features)
        network = conn.get_network(session['network_id']) # get updated network
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