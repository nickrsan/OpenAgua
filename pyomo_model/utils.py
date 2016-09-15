import os
import sys
from requests import post
import json
import logging

import wingdbstub

def create_logger(appname, logfile):
    logger = logging.getLogger(appname)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

class connection(object):

    def __init__(self, url=None, session_id=None, app_name=None, log=None):
        self.url = url
        self.app_name = app_name
        self.session_id = session_id
        self.log = log
        

    def call(self, func, args):
        self.log.info("Calling: %s" % (func))
        headers = {'Content-Type': 'application/json',
                   'sessionid': self.session_id, # this lets us keep the session ID associated with the connection
                   'appname': self.app_name}
        data = json.dumps({func: args})

        response = post(self.url, data=data, headers=headers)
        if not response.ok:
            try:
                fc, fs = response['faultcode'], response['faultstring']
                self.log.debug('Something went wrong. Check faultcode and faultstring.')
                resp = json.loads(response.content)
                err = "faultcode: %s, faultstring: %s" % (fc, fs)
            except:                
                self.log.debug('Something went wrong. Check command sent.')
                self.log.debug("URL: %s"%self.url)
                self.log.debug("Call: %s" % json.dumps(call_json))             

                if response.content != '':
                    err = response.content
                else:
                    err = "Something went wrong. An unknown server has occurred."

            # need to figure out how to raise errors
        
        self.log.info('Finished communicating with Hydra Platform.')

        resp = json.loads(response.content.decode(), object_hook=JSONObject)
        return resp

    def login(self, username=None, password=None):
        if username is None:
            err = 'Error. Username not provided.'
            # raise error
        response = self.call('login', {'username': username, 'password': password})
        self.session_id = response.sessionid
        self.user_id = response.userid
        self.log.info("Session ID: %s", self.session_id)
        return self.session_id
    
    def get_network(self, args):
        get_network_params = dict(
            network_id = eval(args.network_id),
            include_data = 'Y',
            template_id = eval(args.template_id),
            scenario_ids = eval(args.scenario_ids),
            summary = 'N'
        )
        network = self.call('get_network', get_network_params)
        return network
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)


