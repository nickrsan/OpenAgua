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
                fc, fs = response['faultcode'], response['faultstring']
                log.debug('Something went wrong. Check faultcode and faultstring.')
                resp = json.loads(response.content)
                err = "faultcode: %s, faultstring: %s" % (fc, fs)
            except:                
                log.debug('Something went wrong. Check command sent.')
                log.debug("URL: %s"%self.url)
                log.debug("Call: %s" % json.dumps(call_json))             

                if response.content != '':
                    err = response.content
                else:
                    err = "Something went wrong. An unknown server has occurred."

            # need to figure out how to raise errors
        
        log.info('Finished communicating with Hydra Platform.')

        resp = json.loads(response.content, object_hook=JSONObject)
        return resp

    def login(self, username=None, password=None):
        if username is None:
            err = 'Error. Username not provided.'
            # raise error
        response = self.call('login', {'username': username, 'password': password})
        self.session_id = response.session_id
        log.info("Session ID: %s", self.session_id)
        return self.session_id

    # specific methods
    def get_user_by_name(self, username=None):
        if username is None:
            err = 'Error. Username not provided.'
        resp = self.call('get_user_by_name', {'username': username})        
        return resp  
    
    def get_project_by_name(self, project_name=None):
        if project_name is None:
            err = 'Error. Project name not provided'
        resp = self.call('get_project_by_name', {'project_name':project_name})  
        return resp
    
    def get_network_by_name(self, project_id=None, network_name=None):
        if project_id is None:
            err = 'Error. Project ID not provided'
        if network_name is None:
            err = 'Error. Network name not provided'
        resp = self.call('get_network_by_name', {'project_id':project_id, 'network_name':network_name})
        return resp
    
    def add_project(self, project_data=None):
        return self.call('add_project', project_data)
    
    def get_network(self, network_id=None):
        return self.call('get_network', {'network_id':network_id})
    
    def get_geojson_node(self, node_id=None, template_name=None, template_id=None):
        node = self.call('get_node', {'node_id':node_id})
        type_id = [t.id for t in node.types if t.template_id==template_id][0]
        ftype = self.call('get_templatetype',{'type_id':type_id})
        gj = {'type':'Feature',
             'geometry':{'type':'Point',
                         'coordinates':[node.x, node.y]},
             'properties':{'name':node.name,
                           'id':node.id,
                           'description':node.description,
                           'ftype':ftype.name,
                           'image':ftype.layout.image,
                           'template_name':template_name}}
        return gj

    def get_geojson_link(self, link_id=None, template_id=None, coords=None):
        link = self.call('get_link', {'link_id':link_id})
        type_id = [t.id for t in link.types if t.template_id==template_id][0]
        ftype = self.call('get_templatetype',{'type_id':type_id})

        n1 = link['node_1_id']
        n2 = link['node_2_id']
            
        gj = {'type':'Feature',
             'geometry':{ 'type': 'LineString',
                          'coordinates': [coords[n1],coords[n2]] },
             'properties':{'name':link.name,
                           'id':link.id,
                           'description':link.description,
                           'ftype':ftype.name,
                           'image':ftype.layout.image}}
        return gj
    
    # convert geoJson node to Hydra node
    def get_node_from_geojson(self, gj=None, template=None):
        x, y = gj['geometry']['coordinates']
        type_name = gj['properties']['type']
        #type_obj = self.call('get_templatetype_by_name', {'template_id':template_id,'type_name':type_name})
        # the above doesn't work. this should, but will be less efficient...
        type_obj = [t for t in template.types if t.name==type_name][0]
        
        typesummary = dict(
            name = type_obj.name,
            id = type_obj.id,
            template_name = template.name,
            template_id = template.id
        )
        node = dict(
            id = -1,
            name = gj['properties']['name'],
            description = gj['properties']['description'],
            x = str(x),
            y = str(y),
            types = [typesummary]
        )
        return node
    
    
    def get_links_from_geojson(self, gj=None, template=None, coords=None):
        d = 3 # rounding decimal points to match link coords with nodes.
        # p.s. This is annoying. It would be good to have geographic/topology capabilities built in to Hydra
        nlookup = {(round(x,d), round(y,d)): k for k, [x, y] in coords.items()}
        xys = []
        for [x,y] in gj['geometry']['coordinates']:
            xy = (round(x,d), round(y,d))
            xys.append(xy)
        type_name = gj['properties']['type']        
        type_obj = [t for t in template.types if t.name==type_name][0]
        
        typesummary = dict(
            name = type_obj.name,
            id = type_obj.id,
            template_name = template.name,
            template_id = template.id
        )

        links = []
        nsegments = len(xys) - 1        
        for i in range(nsegments):
            link = dict(
                id = -1,
                name = '{}_{:02}'.format(gj['properties']['name'], i+1),
                description = '{} (Segment {})'.format(gj['properties']['description'], i+1),
                node_1_id = nlookup[xys[i]],
                node_2_id = nlookup[xys[i+1]],
                types = typesummary
            )
        
        links.append(link)
        return links   
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)
            
   
