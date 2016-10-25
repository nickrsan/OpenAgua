import os
import sys
from requests import post
import json
import logging
from attrdict import AttrDict

from pyomo.environ import Var

import wingdbstub

def create_logger(appname, logfile, msg_format):
    logger = logging.getLogger(appname)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(msg_format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

class connection(object):

    def __init__(self, args=None, scenario_id=None, template_id=None, log=None):
        self.url = args.hydra_url
        self.app_name = args.app_name
        self.session_id = args.session_id
        self.user_id = args.user_id
        self.log = log
        
        get_network_params = dict(
            network_id = args.network_id,
            include_data = 'Y',
            template_id = args.template_id,
            scenario_ids = [scenario_id],
            summary = 'N'
        )        
        
        response = self.call('get_network', get_network_params)
        if 'faultcode' in response:
            if response['faultcode'] == 'No Session':
                self.session_id = self.login(username=args.hydra_username,
                                                           password=args.hydra_password)
            response = self.call('get_network', get_network_params)
            
        self.network = response
        
        self.template = self.call('get_template', {'template_id': template_id})
        
        # create some useful dictionaries
        # Since pyomo doesn't know about attribute ids, etc., we need to be able to relate
        # pyomo variable names to resource attributes to be able to save data back to the database.
        # the res_attrs dictionary lets us do that by relating pyomo indices and variable names to
        # the resource attribute id.

        # dictionary to store resource attribute dataset types
        self.attr_meta = {}  
        
        # dictionary for looking up attribute ids

        self.attrs = AttrDict()
        for tt in self.template.types:
            res_type = tt.resource_type.lower()
            if res_type not in self.attrs.keys():
                self.attrs[res_type] = AttrDict()
            for ta in tt.typeattrs:
                self.attrs[res_type][ta.attr_id] = AttrDict({
                    'name': ta.attr_name,
                    'name_': ta.attr_name.replace(' ', '_'),
                    'dtype': ta.data_type,
                    'unit': ta.unit,
                    'dim': ta.dimension
                })            
        
        # dictionary to store resource attribute ids
        self.res_attrs = AttrDict({'node': {}, 'link': {}})
        self.attr_ids = {}
        self.res_names = {}
        
        for n in self.network.nodes:
            for ra in n.attributes:
                self.res_attrs['node'][(n.id, self.attrs.node[ra.attr_id]['name_'])] = ra.id
                self.attr_ids[ra.id] = ra.attr_id
                self.res_names[ra.id] = n.name
        
        for l in self.network.links:
            for ra in l.attributes:
                self.res_attrs['link'][(l.node_1_id, l.node_2_id, self.attrs.link[ra.attr_id]['name_'])] = ra.id    
                self.attr_ids[ra.id] = ra.attr_id
                self.res_names[ra.id] = l.name

    def call(self, func, args):
        self.log.debug("Calling: %s" % (func))
        headers = {'Content-Type': 'application/json',
                   'sessionid': self.session_id,
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
        
        self.log.debug('Finished communicating with Hydra Platform.')

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
    
    def save_results(self, instance, outputnames):
        res_scens = {}
        updated_res_scens = []
        scenario = self.network.scenarios[0]
        scenario_id = scenario.id
        for rs in scenario.resourcescenarios:
            res_scens[rs.resource_attr_id] = rs
    
        # loop through all the model variables
        for i, v in enumerate(instance.component_objects(Var, active=True)):
            varname = str(v)
            
            # continue if we aren't interested in this variable (intermediaries...)
            if varname not in outputnames.keys():
                continue
            
            fullname = outputnames[varname]
            
            # the variable object
            varobject = getattr(instance, varname)
            timeseries = {}
            
            # loop through all indices - including all nodes/links and timesteps
            for index in varobject:
                if len(index) == 2:
                    idx = (index[0], fullname)
                    timekey = 1
                else:
                    idx = (index[0], index[1], fullname)
                    timekey = 2
                if idx not in timeseries.keys():
                    timeseries[idx] = {}
                timeseries[idx][self.OAtHPt[index[timekey]]] = varobject[index].value
        
            # save variable data to database
            for idx in timeseries.keys():
                
                ra_id = self.res_attrs.node[idx]
                attr_id = self.attr_ids[ra_id]
                attr = self.attrs.node[attr_id]
                res_name = self.res_names[ra_id]
                dataset_name = '{} for {}'.format(fullname, res_name)
                
                dataset_value = json.dumps({'0': timeseries[idx]})
                #dataset_value = {'0': timeseries[idx]}
                
                #if ra_id not in res_scens.keys():
                    ## create a new dataset
                dataset = {
                    'type': attr.dtype,
                    'name': dataset_name,
                    'unit': attr.unit,
                    'dimension': attr.dim,
                    'value': dataset_value
                }
                self.call('add_data_to_attribute',
                          {'scenario_id': scenario_id, 'resource_attr_id': ra_id, 'dataset': dataset})
                #else:
                    ## just update the existing resourcedata
                    #rs = res_scens[ra_id]
                    ##dataset = res_scens[ra_id].value
                    #rs.value.name = dataset_name
                    #rs.value.value = dataset_value
                    ##updated_res_scen = {
                        ##'resource_attr_id': ra_id,
                        ##'attr_id': attr_id,
                        ##'value': dataset
                    ##}
                    #updated_res_scens.append(rs)
    
        #if updated_res_scens:
            #update = conn.call('update_resourcedata',
                               #{'scenario_id': scenario_id, 'resource_scenarios': updated_res_scens}) 
                               
        #return result
    
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