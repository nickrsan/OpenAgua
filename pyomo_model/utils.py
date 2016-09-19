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

    def __init__(self, args=None, scenario_id=None, log=None):
        self.url = args.hydra_url
        self.app_name = args.app_name
        self.session_id = args.session_id
        self.log = log
        
        get_network_params = dict(
            network_id = args.network_id,
            include_data = 'Y',
            template_id = args.template_id,
            #scenario_ids = [scenario_id],
            summary = 'N'
        )        
        
        response = self.call('get_network', get_network_params)
        
        if 'faultcode' in response:
            if response['faultcode'] == 'No Session':
                self.session_id = self.login(username=args.hydra_username,
                                             password=args.hydra_password)
            response = self.call('get_network', get_network_params)
        self.network = response

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
                self.log.debug("Call: %s" % data)             

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
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)


def parse_function(s):
    s = s.rstrip()
    lines = s.split('\n')
    if 'return ' not in lines[-1]:
        lines[-1] = 'return ' + lines[-1]
    fs = 'def f(date):\n    %s' % '\n    '.join(lines)
    return fs

def eval_function(s, date, **kwargs):
    fs = parse_function(s)
    exec(fs, globals())
    
    return f(date)
