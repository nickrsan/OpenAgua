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
                log.debug("Call: %s" % json.dumps(call_json))             

                if response.content != '':
                    err = response.content
                else:
                    err = "Something went wrong. An unknown server has occurred."

            # need to figure out how to raise errors
        
        log.info('Finished communicating with Hydra Platform.')

        resp_json = json.loads(response.content, object_hook=JSONObject)
        return resp_json

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
    
    def get_geojson_node(self, node_id=None, template_id=None):
        node = self.call('get_node', {'node_id':node_id})
        type_id = [t.id for t in node.types if t.template_id==template_id][0]
        ftype = self.call('get_templatetype',{'type_id'})
        f = {'type':'Feature',
             'geometry':{'type':'Point',
                         'coordinates':[node.x, node.y]},
             'properties':{'name':node.name,
                           'id':node.id,
                           'description':node.description,
                           'type':,
                           'icone':icon}} # hopefully this can be pretty fancy
        gj.append(f)

    return gj        
    
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)
            
   
