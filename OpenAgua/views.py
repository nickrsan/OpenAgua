from flask import jsonify, Response, json, request, session, redirect, url_for, escape, send_file, render_template
from functools import wraps
import random # delete later - used to create randomly distributed test nodes around Monterrey
import requests

#import json

from connection import connection

from OpenAgua import app

#
# connect - this should be done through the interface
#

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

def get_project_by_name(conn, project_name):
    return conn.call('get_project_by_name', {'project_name':project_name})

def get_network_by_name(conn, project_name, network_name):
    project = get_project_by_name(conn, project_name)
    return conn.call('get_network_by_name', {'project_id':project.id, 'network_name':network_name})

def get_network(conn, network_id):
    return conn.call('get_network', {'network_id':network_id})    

# convert hydra nodes to geoJson for Leaflet
def nodes_geojson(nodes, coords):
    gj = []
    for n in nodes:
        if n.types:
            ftype = n.types[0] # assume only one template
            ftype_name = ftype.name
            template_name = ftype.template_name
        else:
            ftype_name = 'UNASSIGNED'
            template_name = 'UNASSIGNED'
        f = {'type':'Feature',
             'geometry':{'type':'Point',
                         'coordinates':coords[n.id]},
             'properties':{'name':n.name,
                           'description':n.description,
                           'nodetype':ftype_name,
                           'template':template_name,
                           'popupContent':'TEST'}} # hopefully this can be pretty fancy
        gj.append(f)
    return gj

def links_geojson(links, coords):
    gj = []
    for l in links:
        n1 = l['node_1_id']
        n2 = l['node_2_id']
        if l.types:
            ftype = l.types[0] # assume only one template
            ftype_name = ftype.name
            template_name = ftype.template_name
        else:
            ftype_name = 'UNASSIGNED'
            template_name = 'UNASSIGNED'
        f = {'type':'Feature',
             'geometry':{ 'type': 'LineString',
                          'coordinates': [coords[n1],coords[n2]] },
             'properties':{'name':l.name,
                           'description':l.description,
                           'linetype':ftype_name,
                           'template':template_name,
                           'popupContent':'TEST'}}

        gj.append(f)

    return gj

def get_coords(network):
    coords = {}
    for n in network['nodes']:
        coords[n.id] = [float(n.x), float(n.y)] 
    return coords


# get shapes of type ftype
def get_shapes(shapes, ftype):
    return [s for s in shapes if s['geometry']['type']==ftype]

# make nodes - formatted as geoJson - from Leaflet
def make_nodes(shapes):
    nodes = []
    for s in shapes:
        x, y = s['geometry']['coordinates']
        n = dict(
            id = -1,
            #name = s['properties']['name'],
            name = 'Point' + str(random.randrange(0,1000)),
            description = 'It\'s a new node!',
            x = str(x),
            y = str(y)
        )
        nodes.append(n)
    return nodes

# make links - formatted as geoJson - from Leaflet
# need to account for multisegment lines
# for now, this assumes links lack vertices
def make_links(polylines, coords):
    d = 4 # rounding decimal points to match link coords with nodes.
    # p.s. This is annoying. It would be good to have geographic/topology capabilities built in to Hydra
    nlookup = {(round(x,d), round(y,d)): k for k, [x, y] in coords.items()}
    links = []
    for pl in polylines:
        xys = []
        for [x,y] in pl['geometry']['coordinates']:
            xy = (round(x,d), round(y,d))
            xys.append(xy)

        l = dict(
            id = -1,
            #name = pl['properties']['name'],
            name = 'Link' + str(random.randrange(0,1000)),
            description = 'It\'s a new link!',
            node_1_id = nlookup[xys[0]],
            node_2_id = nlookup[xys[1]]
        )
        links.append(l)
    return links

def add_network(conn, project_name):
    network = conn.call('add_network', {'net':{'nodes':[], 'links':[]}})       

# use this to add shapes from Leaflet to Hydra
def add_features(conn, network_id, shapes):

    # modify to account for possibly no network... create network instead of add node

    # convert geoJson to Hydra features & write to Hydra
    points = get_shapes(shapes, 'Point')
    polylines = get_shapes(shapes, 'LineString')    

    if points:
        nodes = make_nodes(points)
        if nodes:
            nodes = conn.call('add_nodes', {'network_id': network_id, 'nodes': nodes})
    if polylines:
        network = get_network(conn, network_id)
        coords = get_coords(network)                   
        links = make_links(polylines, coords)
        if links:                         
            links = conn.call('add_links', {'network_id': network_id, 'links': links})

def get_features(network):
    coords = get_coords(network)
    nodes = nodes_geojson(network.nodes, coords)
    links = links_geojson(network.links, coords)
    features = nodes + links
    return features

#
# Set up project. To be deleted once we can integrate into the UI.
#

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
            return redirect(url_for('login'))
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
    return redirect(url_for('login'))

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
        status_message = 'Edits saved'
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