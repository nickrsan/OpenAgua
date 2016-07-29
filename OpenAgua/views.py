from __future__ import print_function
from flask import jsonify, Response, json, request, session, redirect, url_for, escape, send_file, render_template
from flask import Markup
from functools import wraps
import requests
import sys

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
            session['username'] = username
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

    # connect to hydra (login if we don't already have a session ID)
    if 'session_id' in session:
        conn = connection(url=url, session_id=session['session_id'])
    else:
        conn = connection(url=url)
    
    # this makes sure we are logged in, in case there is a leftover session_id
    # in the Flask session. We shouldn't get here though.
    conn.login(username = hydra_username, password = hydra_password)    
    session['session_id'] = conn.session_id
        
    user = conn.get_user_by_name(hydra_username)
    session['user_id'] = user.id

    projects = conn.call('get_projects',{'user_id':session['user_id']})
    project_names = [project.name for project in projects]
    return render_template('home.html',
                           project_names = project_names)

@app.route('/network_editor')
@login_required
def network_editor():
    conn = connection(url=url, session_id=session['session_id'])
    template = conn.call('get_template', {'template_id':session['template_id']})
    ntypes = [t.name for t in template.types if t.resource_type == 'NODE']
    ltypes = [t.name for t in template.types if t.resource_type == 'LINK']
    
    return render_template('network_editor.html',
                           ntypes=ntypes, ltypes=ltypes) 

# Load projects
# in the future, we can (optionally) store the Hydra session ID with the user account
# i.e., give the user an option to auto-load last-used project.
@app.route('/_load_recent')
def load_recent():
    
    conn = connection(url=url, session_id=session['session_id'])
    
    # load recent project / network (to be done by user in the future)
    session['project_name'] = app.config['HYDRA_PROJECT_NAME']
    session['network_name'] = app.config['HYDRA_NETWORK_NAME']    
    
    # load / create project
    project = conn.get_project_by_name(session['project_name'])
    session['project_id'] = project.id

    # load / activate network
    network = conn.get_network_by_name(session['project_id'], session['network_name'])
    session['network_id'] = network.id
    activated = conn.call('activate_network', {'network_id':session['network_id']})
    
    # load / activate template (temporary fix)
    # NB: "get_template_by_name" in Hydra doesn't work!!!
    #session['template_id'] = 5 # this works on David's office computer only.
    session['template_id'] = 4 # this works on David's home computer only.
    session['template_name'] = 'WEAP'
    
    return redirect(url_for('network_editor'))

@app.route('/_add_project', methods=['GET', 'POST'])
def add_project():
    conn = connection(url=url, session_id=session['session_id'])
    proj = dict(
        name = request.form['project_name'],
        description = request.form['project_description']
    )
    project = conn.add_project(proj)
    return redirect(url_for('home'))

@app.route('/_add_network', methods=['GET', 'POST'])
def add_network():
    conn = connection(url=url, session_id=session['session_id'])
    net = dict(
        project_id = session['project_id'],
        name = request.form['network_name'],
        description = request.form['network_description']
    )
    network = conn.call('add_network', {'net':net})
    return redirect(url_for('home'))

@app.route('/_load_network')
def load_network():
    conn = connection(url=url, session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    template = conn.call('get_template',{'template_id':session['template_id']})
    
    #features = features2gj(network, template)
    coords = get_coords(network)
    nodes = network.nodes
    links = network.links
    nodes_gj = [conn.get_geojson_node(node.id, session['template_id']) for node in nodes if nodes]
    links_gj = [conn.get_geojson_link(link.id, session['template_id'], coords) for link in links if links]
    features = nodes + links

    status_code = 1
    status_message = 'Network "%s" loaded' % session['network_name']

    features = json.dumps(features)
    
    result = dict(features=features, status_code=status_code, status_message=status_message)
    result_json = jsonify(result=result)
    return result_json

@app.route('/_save_network')
def save_network():
    conn = connection(url=url, session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    templates = [conn.call('get_template', {'template_id':t.template_id}) for t in network.types]
    template = templates[0]    
    features = get_features(network, template)

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

@app.route('/_add_feature')
def add_feature():
    conn = connection(url=url, session_id=session['session_id'])
    network = conn.get_network(session['network_id'])

    new_feature = request.args.get('new_feature')
    gj = json.loads(new_feature)

    new_gj = ''
    status_code = -1
    if gj['geometry']['type'] == 'Point':
        if gj['properties']['name'] not in [f.name for f in network.nodes]:
            node_new = conn.make_node_from_geojson(gj, session['template_name'], session['template_id'])
            node = conn.call('add_node', {'network_id':session['network_id'], 'node':node_new})
            new_gj = hyd2gj_nodes([node]) # let's just send back what we got to save time (for now)
            status_code = 1
    else:
        if gj['properties']['name'] not in [f.name for f in network.links]:
            coords = get_coords(network)
            links = conn.call('add_links', {'network_id':session['network_id'], 'links':gj2hyd_polyline(gj, coords)})
            new_gj = hyd2gj_links(links, coords)
            status_code = 1
    result = dict(new_gj = new_gj, status_code = status_code)
    return jsonify(result=result)

@app.route('/_delete_feature')
def delete_feature():
    conn = connection(url=url, session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    
    deleted_feature = request.args.get('deleted')
    gj = json.loads(deleted_feature)

    status_code = -1
    if gj['geometry']['type'] == 'Point':
        conn.call('delete_node',{'node_id': gj['properties']['id']})
        status_code = 1
    else:
        conn.call('delete_link',{'link_id': gj['properties']['id']})
        status_code = 1
    return jsonify(result=dict(status_code=status_code))

@app.route('/settings')
@login_required
def settings():   
    return render_template('settings.html')

@app.route('/_hydra_call')
def hydra_call():
    s = request.args.get('request')
    j = json.loads(s)
    resp = conn.call(j['func'], j['args'])
    return jsonify(result=dict(response=resp))