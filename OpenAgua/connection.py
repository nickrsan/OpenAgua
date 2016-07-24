import requests
import json

import logging
log = logging.getLogger(__name__)

class connection(object):

    def __init__(self, url=None, session_id=None, app_name=None):
        self.url = url
        self.app_name = app_name
        self.session_id = session_id

    def call(self, func, args):
        log.info("Calling: %s" % (func))
        headers = {'Content-Type': 'application/json',
                   'sessionid': self.session_id, # this lets us keep the session ID associated with the connection
                   'appname': self.app_name}
        call_json = {func: args}

        response = requests.post(self.url, json=call_json, headers=headers)
        if not response.ok:
            try:
                fc, fs = resp['faultcode'], resp['faultstring']
                log.debug('Something went wrong. Check faultcode and faultstring.')
                resp = json.loads(response.content)
                err = "faultcode: %s, faultstring: %s" % (fc, fs)
            except:                
                log.debug('Something went wrong. Check command sent.')
                log.debug("URL: %s"%self.url)
                log.debug("Call: %s" % json.dumps(call))             

                if response.content != '':
                    err = response.content
                else:
                    err = "Something went wrong. An unknown server has occurred."

            raise RequestError(err)
        
        log.info('Finished communicating with Hydra Platform.')

        resp_json = json.loads(response.content, object_hook=JSONObject)
        return resp_json

    def login(self, username=None, password=None):
        if username is None:
            err = 'Error. No username supplied.'
            raise RequestError(err)
        response = self.call('login', {'username': username, 'password': password})

        self.session_id = response.session_id

        log.info("Session ID: %s", self.session_id)

        return self.session_id
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)
            
def get_project_by_name(conn, project_name):
    return conn.call('get_project_by_name', {'project_name':project_name})

def get_network_by_name(conn, project_name, network_name):
    project = get_project_by_name(conn, project_name)
    return conn.call('get_network_by_name', {'project_id':project.id, 'network_name':network_name})

def get_network(conn, network_id):
    return conn.call('get_network', {'network_id':network_id})    

def get_coords(network):
    coords = {}
    for n in network['nodes']:
        coords[n.id] = [float(n.x), float(n.y)] 
    return coords

# get shapes of type ftype
def get_shapes(shapes, ftype):
    return [s for s in shapes if s['geometry']['type']==ftype]

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
