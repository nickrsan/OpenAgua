import os
from webcolors import name_to_hex
import sys
import requests
import json
from copy import deepcopy
from flask import session
from flask_security import current_user
import zipfile
from attrdict import AttrDict

import logging

from .utils import hydra_timeseries, eval_data, encrypt, decrypt
from .models import User, HydraUser, HydraUrl, HydraStudy
from . import app # delete later

log = logging.getLogger(__name__)

def get_coords(nodes):
    coords = {}
    for n in nodes:
        coords[n.id] = [float(n.x), float(n.y)] 
    return coords

class connection(object):

    def __init__(self, url=None, session_id=None,
                 user_id=None, app_name=None,
                 project_id=None, project_name=None,
                 network_id=None, network_name=None,
                 template_id=None, template_name=None,
                 ttypes=None):
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

        resp = json.loads(response.content.decode("utf-8"),
                          object_hook=JSONObject)
        return resp

    def login(self, username=None, password=None):
        if username is None:
            err = 'Error. Username not provided.'
            # raise error
        response = self.call('login', {'username': username,
                                       'password': password})
        self.session_id = response.sessionid
        self.user_id = response.userid
        log.info("Session ID: %s", self.session_id)

    # specific methods
    def get_user_by_name(self, username=None):
        if username is None:
            err = 'Error. Username not provided.'
        resp = self.call('get_user_by_name', {'username': username})        
        return resp
    
    def get_project(self, project_id=None):
        return self.call('get_project', {'project_id': project_id})
    
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
        resp = self.call('get_network_by_name',
                         {'project_id':project_id, 'network_name':network_name})
        return resp
    
    def add_project(self, project_data=None):
        return self.call('add_project', project_data)
    
    def get_network(self, network_id=None, include_data='N'):
        return self.call('get_network', {'network_id':network_id,
                                         include_data: include_data})
    
    def get_template(self, template_id=None):
        return self.call('get_template', {'template_id':template_id})
    
    def get_node(self, node_id=None):
        return self.call('get_node',{'node_id':node_id})
    
    def purge_replace_node(self, gj=None):
        
        node_id = gj['properties']['id']
        
        # update existing attached links
        links = [l for l in self.network.links if node_id in [l.node_1_id, l.node_2_id]]
        if links:
            if len(links) > 1:
                replacement_node = 'Junction'
                lname = ' + '.join([l.name for l in links])
                node_name = '{} {}'.format(lname, replacement_node)
            elif links[0].node_1_id == node_id:
                replacement_node = 'Inflow'
                lname = links[0].name
                node_name = '{} {}'.format(lname, replacement_node)
            else:
                replacement_node = 'Outflow'
                lname = links[0].name
                node_name = '{} {}'.format(lname, replacement_node)
            xy = [float(i) for i in gj['geometry']['coordinates']]
            new_node = self.make_generic_node(replacement_node, xy, node_name)
            if 'faultcode' in new_node and 'already in network' in new_node.faultstring:
                new_node = [n for n in self.network.nodes if n.name==node_name][0]
            self.update_links(node_id, new_node.id)
        else:
            new_node = None
            
        # purge node
        self.call('purge_node', {'node_id': node_id, 'purge_data': 'Y'})        
        
        return new_node
        
    def update_links(self, old_node_id, new_node_id):
        for link in self.network.links:
            if old_node_id in [link.node_1_id, link.node_2_id]:
                new_link = link.__dict__
                if link.node_1_id == old_node_id:
                    new_link['node_1_id'] = new_node_id
                elif link.node_2_id == old_node_id:
                    new_link['node_2_id'] = new_node_id
                updated_link = self.call('update_link', {'link': new_link})
        return
    
    def make_geojson_from_node(self, node=None):
        type_id = [t.id for t in node.types \
                   if t.template_id==self.template.id][0]
        ttype = self.ttypes[type_id]
        gj = {'type':'Feature',
              'geometry':{'type':'Point',
                          'coordinates':[node.x, node.y]},
              'properties':{'name':node.name,
                            'id':node.id,
                            'description':node.description,
                            'template_type_name':ttype.name,
                            'template_type_id':ttype.id,
                            'image':ttype.layout.image,
                            'template_name':self.template.name}}
        return gj

    def make_geojson_from_link(self, link=None):
        
        coords = get_coords(self.network.nodes)
        
        type_id = [t.id for t in link.types \
                   if t.template_id==self.template.id][0]
        ttype = self.ttypes[type_id]

        n1_id = link['node_1_id']
        n2_id = link['node_2_id']
        
        # for dash arrays, see:
        # https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/stroke-dasharray
        symbol = ttype.layout.symbol
        if symbol=='solid':
            dashArray = '1,0'
        elif symbol=='dashed':
            dashArray = '5,5'
            
        gj = {'type':'Feature',
             'geometry':{ 'type': 'LineString',
                          'coordinates': [coords[n1_id],coords[n2_id]] },
             'properties':{'name':link.name,
                           'id':link.id,
                           'description':link.description,
                           'template_type_name':ttype.name,
                           'template_type_id':ttype.id,
                           'image':ttype.layout.image,
                           'template_name':self.template.name,
                           'color': name_to_hex(ttype.layout.colour),
                           'weight': ttype.layout.line_weight,
                           'opacity': 0.7,
                           'dashArray': dashArray,
                           'lineJoin': 'round'
                           }
             }
        return gj
        
    # make geojson features
    def make_geojson_features(self):
        
        nodes_gj = \
            [self.make_geojson_from_node(node) for node in self.network.nodes]
        
        links_gj = \
            [self.make_geojson_from_link(link) \
             for link in self.network.links]

        features = nodes_gj + links_gj
    
        return features
    
    # convert geoJson node to Hydra node
    def add_node_from_geojson(self, gj=None, existing_node_id=None):
        x, y = gj['geometry']['coordinates']
        ttype_name = gj['properties']['template_type_name']
        ttype_id = int(gj['properties']['template_type_id'])
        
        typesummary = dict(
            name = ttype_name,
            id = ttype_id,
            template_name = self.template.name,
            template_id = self.template.id
        )
        node = dict(
            id = -1,
            name = gj['properties']['name'],
            description = gj['properties']['description'],
            x = str(x),
            y = str(y),
            types = [typesummary]
        )
        
        # delete old node
        # will be faster to get this client side from Leaflet Snap
        old_node_id = None
        for n in self.network.nodes:
            if (x,y) == (float(n.x), float(n.y)):
                old_node_id = n.id
                break
        
        # add new node
        new_node = self.call('add_node', {'network_id': session['network_id'], 'node': node})
        
        # update existing adjacent links, if any, with new node id
        # it would be best if we could get the attached links clientside
        if old_node_id:
            self.update_links(old_node_id, new_node.id)
            self.call('purge_node', {'node_id': old_node_id})
        
        return new_node
    
    def make_generic_node(self, ttype_name, xy, node_name):
        typesummary = dict(
            name = ttype_name,
            id = self.ttype_dict[ttype_name],
            template_name = self.template.name,
            template_id = self.template.id
        )
        node = dict(
            id = -1,
            name = node_name,
            description = '%s added automatically' % ttype_name,
            x = str(xy[0]),
            y = str(xy[1]),
            types = [typesummary]
        )
            
        hydra_node = self.call('add_node',
                               {'network_id': self.network.id,
                                'node': node})          
        return hydra_node
    
    def make_links_from_geojson(self, gj=None):        
        
        coords = get_coords(self.network.nodes)
        
        d = 3 # rounding decimal points to match link coords with nodes.
        nlookup = {(round(x,d), round(y,d)): k for k, [x, y] in coords.items()}
        xys = []
        for [x,y] in gj['geometry']['coordinates']:
            xy = (round(x,d), round(y,d))
            xys.append(xy)
        
        lname = gj['properties']['name'] # link name
        desc = gj['properties']['description']
        ttype_name = gj['properties']['template_type_name']
        ttype_id = int(gj['properties']['template_type_id'])
        
        typesummary = dict(
            name = ttype_name,
            id = ttype_id,
            template_name = self.template.name,
            template_id = self.template.id
        )

        links = []
        hnodes = [] # extra nodes created
        nsegments = len(xys) - 1
        segments = range(nsegments)
        for i in segments:
            
            segnodes = {}
            for x, n in enumerate([1,2]):
                xy = xys[i+x]
                if xy in nlookup:
                    node_id = nlookup[xy]
                else:
                    if i==segments[0] and n==1:
                        node_type = 'Inflow'
                    elif i==segments[-1] and n==2:
                        node_type = 'Outflow'
                    else:
                        node_type = 'Junction'
                    node_name = '{} ({},{})'.format(lname, xy[0], xy[1])
                    hnode = self.make_generic_node(node_type, xy, node_name) 
                    hnodes.append(hnode)
                    node_id = hnode.id
                    nlookup[xy] = node_id
                
                segnodes[n] = node_id

            node_1_id = segnodes[1]
            node_2_id = segnodes[2]
            link = {'node_1_id': node_1_id, 'node_2_id': node_2_id,
                    'types': [typesummary]}
            if not desc:
                desc = '{} [{}]'.format(lname, ttype_name)
            if len(lname) and nsegments == 1:
                link['name'] = lname
                link['description'] = desc
            elif len(lname) and nsegments > 1:
                link['name'] = '{} {:02}'.format(lname, i+1)
                link['description'] = '{} (Segment {})'.format(desc, i+1)
            else:
                n1_name = self.get_node(node_1_id).name
                n2_name = self.get_node(node_2_id).name
                link['name'] = '{} to {}'.format(n1_name, n2_name)
                link['description'] = '{} from {} to {}' \
                    .format(ttype_name, n1_name, n2_name)
                
            links.append(link)
        
        hlinks = self.call('add_links',
                                {'network_id': self.network.id,
                                 'links': links})
        
        return hlinks, hnodes
    
    def load_active_study(self):
        study = HydraStudy.query \
            .filter(HydraStudy.user_id == current_user.id) \
            .filter(HydraStudy.active == 1) \
            .first()
        
        self.invalid_study = False
        if study:
            
            # get project
            
            self.project = self.get_project(study.project_id)
            if 'faultcode' in self.project:
                self.project = None
                session['project_id'] = None
                self.invalid_study = True
            else:
                session['project_id'] = study.project_id
            
            # get network
            self.network = self.get_network(study.network_id)
            if 'faultcode' in self.network:
                self.network = None
                session['network_id'] = None
                self.invalid_study = True
            else:
                session['network_id'] = study.network_id                
            
            # get template
            self.template = self.get_template(study.template_id)
            if 'faultstring' in self.template:
                self.template = None
                self.ttypes = None
                session['template_id'] = None
                self.invalid_study = True
            else:
                session['template_id'] = study.template_id
                
                self.ttypes = {}
                self.ttype_dict = {}
                for ttype in self.template.types:
                    self.ttypes[ttype.id] = ttype
                    self.ttype_dict[ttype.name] = ttype.id 
                                
        else:
            self.invalid_study = True
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)                            
            
def make_connection():
        
    conn = connection(url=session['hydra_url'],
                      session_id=session['hydra_sessionid'])
    ping = conn.call('get_username', {'uid': session['hydra_userid']})
    
    if 'faultcode' in ping and ping.faultcode == 'No Session':
        conn = connection(url=session['hydra_url'])
        # NOT SECURE IN TRANSMISSION
        conn.login(username=session['hydra_username'],
                   password=decrypt(session['hydra_password'],
                                    app.config['SECRET_ENCRYPT_KEY']))
        session['hydra_sessionid'] = conn.session_id
        
        # ALSO: need to add to database 
    
    return conn

def save_data(conn, old_data_type, cur_data_type, res_attr, res_attr_data, new_value,
              metadata, scen_id):

    if cur_data_type == 'function':
        new_data_type = 'timeseries'
        metadata['function'] = new_value
        new_value = json.dumps(hydra_timeseries(eval_data('generic', "''")))
    else:
        new_data_type = cur_data_type
        metadata['function'] = ''

    # has the data type changed?
    if new_data_type != old_data_type:
        # 1. copy old typeattr:
        old_typeattr = {'attr_id': res_attr['attr_id'],
                        'type_id': res_attr['type_id']}
        # 2. delete the old typeattr
        result = conn.call('delete_typeattr', {'typeattr': old_typeattr})
        # 3. update the old typeattr with the new data type
        new_typeattr = old_typeattr
        new_typeattr['attr_is_var'] = 'N'
        new_typeattr['data_type'] = new_data_type
        new_typeattr['unit'] = res_attr['unit']
        # 3. add the new typeattr
        result = conn.call('add_typeattr', {'typeattr': new_typeattr})
                
    if res_attr_data is None: # add a new dataset
        
        dataset = dict(
            id=None,
            name = res_attr['res_attr_name'],
            unit = res_attr['unit'],
            dimension = res_attr['dimension'],
            type = new_data_type,
            value = new_value,
            metadata = json.dumps(metadata)
        )
        
        args = {'scenario_id': scen_id,
                'resource_attr_id': res_attr['res_attr_id'],
                'dataset': dataset}
        result = conn.call('add_data_to_attribute', args)  
            
    else: # just update the existing dataset
        dataset = res_attr_data['value']
        dataset['type'] = new_data_type
        dataset['value'] = new_value
        dataset['metadata'] = json.dumps(metadata)
        
        result = conn.call('update_dataset', {'dataset': dataset})
        
    if 'faultcode' in result.keys():
        returncode = -1
    else:
        returncode = 1
    return returncode    
    
def create_hydrauser(db,
                     user_id,
                     hydra_url, encrypt_key,
                     hydra_admin_username, hydra_admin_password,
                     hydra_user_username, hydra_user_password):
    hydraurl = HydraUrl.query \
        .filter(HydraUrl.hydra_url == hydra_url).first()

    if hydraurl is None: # this should be done via manage.py, not here
        hydraurl = HydraUrl(hydra_url=hydra_url)
        db.session.add(hydraurl)
        db.session.commit()

        hydraurl = HydraUrl.query \
            .filter(HydraUrl.hydra_url == hydra_url).first()

    # create new Hydra user account
    hydra_user_pw_encrypted = encrypt(hydra_user_password, encrypt_key)        
    conn = connection(url=hydra_url)
    conn.login(username=hydra_admin_username, # UNSECURE TRANSMISSION!
               password=hydra_admin_password) 
    hydra_user = conn.call('get_user_by_name',
                           {'username':hydra_user_username})
    hydrauser = False
    if hydra_user:
        conn.call('update_user_password',
                  {'user_id': hydra_user.id,
                   'new_password': hydra_user_password})
        
        hydrauser = HydraUser.query \
            .filter(HydraUser.hydra_username == hydra_user.username).first()
        if hydrauser: # update hydrauser record
            hydrauser.hydra_userid = hydra_user.id
            hydrauser.hydra_password = hydra_user_pw_encrypted

    else:
        hydra_user = conn.call('add_user',
                               {'user': {'username': hydra_user_username,
                                         'password': hydra_user_password}})

    # add hydra user & session information to database
    if not hydrauser:
        hydrauser = HydraUser( \
            user_id = user_id,
            hydra_url_id = hydraurl.id,
            hydra_userid = hydra_user.id,
            hydra_username = hydra_user.username,
            hydra_password = hydra_user_pw_encrypted,
        )
        db.session.add(hydrauser)
    db.session.commit()
    
    session['hydra_username'] = hydrauser.hydra_username
    session['hydra_password'] = hydrauser.hydra_password

def load_hydrauser():

    hydrauser = HydraUser.query \
        .filter(HydraUser.user_id==session['user_id']).first()
    hydraurl = HydraUrl.query \
        .filter(HydraUrl.id==hydrauser.hydra_url_id).first()

    session['hydrauser_id'] = hydrauser.id
    session['hydra_url'] = hydraurl.hydra_url
    session['hydra_userid'] = hydrauser.hydra_userid
    session['hydra_username'] = hydrauser.hydra_username
    session['hydra_password'] = hydrauser.hydra_password # it's encrypted
    session['hydra_sessionid'] = hydrauser.hydra_sessionid


def add_default_template(conn, template_name):
    
    # load / activate template
    templates = conn.call('get_templates',{})
    if not templates or template_name not in [t.name for t in templates]:
        zf = zipfile.ZipFile(app.config['TEMPLATE_FILE'])
        template_xml = zf.read('OpenAgua/template/template.xml')
        default_tpl \
            = conn.call('upload_template_xml',
                        {'template_xml': template_xml.decode()})
    else:
        default_tpl = [t for t in templates if t.name==template_name][0]
    return default_tpl
        
def add_default_project(conn):

    # add project
    project = conn.call('get_project_by_name',
                        {'project_name': session['hydra_username']})
    
    if 'faultstring' in project:
        project = dict(
            name = session['hydra_username'],
            description = 'Default project created for %s %s (%s)' \
            % (current_user.firstname, current_user.lastname, current_user.email),
        )
        project = conn.call('add_project', {'project':project})
        
    return project


def add_default_network(conn, project_id, template_id, scenario_name):

    network_name = 'Default network'
    
    network = conn.call('get_network_by_name',
                        {'project_id':project_id,
                         'network_name': network_name})
    if 'faultstring' in network and 'not found' in network.faultstring:
        net = dict(
            name = network_name,
            description = 'Default network created for %s %s (%s)' \
            % (current_user.firstname, current_user.lastname, current_user.email),
            project_id = project_id
        )
        
        network = conn.call('add_network', {'net': net})
    
        conn.call('apply_template_to_network',
                      {'template_id': template_id,
                       'network_id': network.id})
        
        # add scenario
        scen = {'name': scenario_name,
                    'description': 'Default OpenAgua scenario',
                    'time_step': 'month'}
        scenario = conn.call('add_scenario',
                             {'network_id': network.id, 'scen': scen})
    return network


def activate_study(db, hydrauser_id, project_id, network_id):
    
    # deactivate other studies
    HydraStudy.query \
        .filter(HydraStudy.user_id == current_user.id).update({'active': 0})
    db.session.commit()
    
    # activate current study
    HydraStudy.query \
        .filter(HydraStudy.hydrauser_id == hydrauser_id) \
        .filter(HydraStudy.project_id == project_id) \
        .filter(HydraStudy.network_id == network_id) \
        .update({'active': 1})        
    db.session.commit()

def add_hydrastudy(db, **kwargs):

    hydrastudy = HydraStudy()
    for k, v in kwargs.items():
        exec('hydrastudy.{} = {}'.format(k, v))
    db.session.add(hydrastudy)
    if 'active' in kwargs and kwargs['active']:
        activate_study(db, kwargs['hydrauser_id'],
                       kwargs['project_id'], kwargs['network_id'])
    db.session.commit()

def add_default_study(conn, db, template_name, hydrauser_id, scenario_name):
    template = add_default_template(conn, template_name) # should be done with manage.py
    project = add_default_project(conn)
    network = add_default_network(conn, project.id, template.id, scenario_name)
    
    add_hydrastudy(db,
        user_id = current_user.id,
        hydrauser_id = hydrauser_id,
        project_id = project.id,
        network_id = network.id,
        template_id = template.id,
        active = 1
    )
