import sys
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
        data = json.dumps({func: args})

        response = requests.post(self.url, data=data, headers=headers)
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
        self.session_id = response.sessionid
        self.user_id = response.userid
        log.info("Session ID: %s", self.session_id)
        return self.session_id
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)
            
   
