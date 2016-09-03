from __future__ import print_function
from webcolors import name_to_hex
import sys
import requests
import json

import logging
log = logging.getLogger(__name__)

class connection(object):

    def __init__(self, url=None, session_id=None, user_id=None, app_name=None):
        self.url = url
        self.app_name = app_name
        self.session_id = session_id
        self.user_id = user_id

    def call(self, func, args):
        log.info("Calling: %s" % (func))
        headers = {'Content-Type': 'application/json',
                   'sessionid': self.session_id,
                   'appname': self.app_name}
        
        data = json.dumps({func: args})

        response = requests.post(self.url, data=data, headers=headers)
        if not response.ok:
            try:
                fc, fs = response['faultcode'], response['faultstring']
                log.debug('Something went wrong. Check faultcode and faultstring.')
                resp = json.loads(response.content.decode("utf-8"))
                err = "faultcode: %s, faultstring: %s" % (fc, fs)
            except:                
                log.debug('Something went wrong. Check command sent.')
                log.debug("URL: %s"%self.url)
                log.debug("Function called: %s" % json.dumps(func))             

                if response.content != '':
                    err = response.content
                else:
                    err = "Something went wrong. An unknown server has occurred."

            # need to figure out how to raise errors
        
        log.info('Finished communicating with Hydra Platform.')

        resp = json.loads(response.content.decode("utf-8"), object_hook=JSONObject)
        return resp

    def login(self, username=None, password=None):
        if username is None:
            err = 'Error. Username not provided.'
            # raise error
        response = self.call('login', {'username': username, 'password': password})
        self.session_id = response.sessionid
        self.user_id = response.userid
        log.info("Session ID: %s", self.session_id)

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
    
    def get_node(self, node_id=None):
        return self.call('get_node',{'node_id':node_id})
    
    def make_geojson_from_node(self, node_id=None, template_name=None, template_id=None):
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

    def make_geojson_from_link(self, link_id=None, template_id=None, template_name=None, coords=None):
        
        link = self.call('get_link', {'link_id':link_id})
        #type_id = [t.id for t in link.types if t.template_id==template_id][0]
        type_obj = link.types[0] # NB: the above line should work. delete this when debugged.
        type_id = type_obj.id
        ttype = self.call('get_templatetype',{'type_id':type_id})

        n1 = link['node_1_id']
        n2 = link['node_2_id']
        
        # for dash arrays, see:
        # https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/stroke-dasharray
        symbol = ttype.layout.symbol
        if symbol=='solid':
            dashArray = '1,0'
        elif symbol=='dashed':
            dashArray = '5,5'
            
        gj = {'type':'Feature',
             'geometry':{ 'type': 'LineString',
                          'coordinates': [coords[n1],coords[n2]] },
             'properties':{'name':link.name,
                           'id':link.id,
                           'description':link.description,
                           'template_type':ttype.name,
                           'image':ttype.layout.image,
                           'template_name':template_name,
                           'color': name_to_hex(ttype.layout.colour),
                           'weight': ttype.layout.line_weight,
                           'opacity': 0.7,
                           'dashArray': dashArray,
                           'lineJoin': 'round'
                           }
             }
        return gj
    
    # convert geoJson node to Hydra node
    def make_node_from_geojson(self, gj=None, template=None):
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
    
    
    def make_links_from_geojson(self, gj=None, template=None, coords=None):
        d = 3 # rounding decimal points to match link coords with nodes.
        # p.s. This is annoying. It would be good to have geographic/topology capabilities built in to Hydra
        nlookup = {(round(x,d), round(y,d)): k for k, [x, y] in coords.items()}
        xys = []
        for [x,y] in gj['geometry']['coordinates']:
            xy = (round(x,d), round(y,d))
            xys.append(xy)
        type_name = gj['properties']['type']        
        type_obj = [t for t in template.types if t.name==type_name][0]
        type_name = type_obj.name
        
        polyline_name = gj['properties']['name']
        description = gj['properties']['description']
        
        typesummary = dict(
            name = type_name,
            id = type_obj.id,
            template_name = template.name,
            template_id = template.id
        )

        links = []
        nsegments = len(xys) - 1        
        for i in range(nsegments):
            
            print(nlookup, file=sys.stderr)
            print(xys[i], file=sys.stderr)
            node_1_id = nlookup[xys[i]]
            node_2_id = nlookup[xys[i+1]]

            link = dict(
                node_1_id = node_1_id,
                node_2_id = node_2_id,
                types = [typesummary]
            )
            if len(polyline_name) and nsegments == 1:
                link['name'] = polyline_name
                link['description'] = description
            elif len(polyline_name) and nsegments > 1:
                link['name'] = '{}_{:02}'.format(polyline_name, i+1)
                link['description'] = '{} (Segment {})'.format(description, i+1)
            else:
                n1_name = self.get_node(node_1_id).name
                n2_name = self.get_node(node_2_id).name
                link['name'] = '{}_{}'.format(n1_name, n2_name)
                link['description'] = '{} from {} to {}'.format(type_name, n1_name, n2_name)
                
        links.append(link)
        return links  
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)
            
   
