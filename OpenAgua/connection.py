import os
from webcolors import name_to_hex
import sys
import requests
import json
from flask import session, flash
from flask_security import current_user
import zipfile
from attrdict import AttrDict

import logging

from .utils import hydra_timeseries, empty_hydra_timeseries, eval_data, encrypt, decrypt
from .models import User, HydraUser, HydraUrl, Study, Chart, InputSetup
from . import app, db # delete later

log = logging.getLogger(__name__)

def get_coords(nodes):
    coords = {}
    for n in nodes:
        coords[n.id] = [float(n.x), float(n.y)] 
    return coords

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
    
    def add_default_project(self):
    
        project_name = current_user.email
        project_description = 'Default project created for {} {} ({})'.format(
            current_user.firstname,
            current_user.lastname,
            current_user.email
        )        
    
        # add project
        project = self.call('add_project', {'project': {'name': project_name, 'description': project_description}})
            
        return project
    
    
    def get_network(self, network_id=None, include_data=False):
        include_data = {False: 'N', True: 'Y'}[include_data]
        return self.call('get_network', {'network_id':network_id,
                                         include_data: include_data})
    
    def get_scenarios(self, network_id=None):
        return self.call('get_scenarios', {'network_id': network_id})
    
    def get_template(self, template_id=None):
        return self.call('get_template', {'template_id':template_id})
    
    def get_node(self, node_id=None):
        return self.call('get_node',{'node_id':node_id})
    
    def get_link(self, link_id=None):
        return self.call('get_link',{'link_id':link_id})

    def add_template_from_json(template, basename, version):
        new_tpl = AttrDict(template.copy())
        new_tpl.name = '{}_v{}'.format(basename, version)
        
        # copy old template directory
        tpl_dir = app.config['UPLOADED_TEMPLATES_DEST']
        src = os.path.join(tpl_dir, template.name)
        dst = os.path.join(tpl_dir, new_tpl.name)
        shutil.copytree(src, dst)
        #old_tpl = os.path.join(tpl_dir, 'template', 'template.xml')
        #if os.path.exists(old_tpl):
            #os.remove(old_tpl) # old xml is obsolete
        
        # genericize the template
        def visit(path, key, value):
            if key in set(['cr_date']):
                return False
            elif key in set(['id', 'template_id', 'type_id', 'attr_id']):
                return key, None            
            return key, value
        new_tpl = remap(dict(new_tpl), visit=visit)
        
        new_template = self.call('add_template', {'tmpl': new_tpl})
        
        return new_template
    
    def purge_replace_node(self, gj=None):
        
        new_link = None
        
        node_id = gj.properties.id
        
        ttype = gj.properties.template_type_name
        
        adj_links = [l for l in self.network.links \
                 if node_id in [l.node_1_id, l.node_2_id]]
        
        if ttype == 'Junction':
            new_node = None
            del_link_ids = [l.id for l in adj_links]
            
            # delete the downstream node and modify the upstream node
            if len(adj_links) == 2 \
               and (adj_links[0].node_2_id == adj_links[1].node_1_id or adj_links[1].node_2_id == adj_links[0].node_1_id):
                uplink = [l for l in adj_links if l.node_2_id == node_id][0]
                downlink = [l for l in adj_links if l.node_1_id == node_id][0]
                uplink['node_2_id'] = downlink.node_2_id
                new_link = self.call('update_link', {'link': uplink})
                self.call('purge_link', {'link': downlink})
        elif ttype == 'Inflow':
            new_node = None
            del_link_ids = [l.id for l in adj_links]
        elif ttype == 'Outflow':
            new_node = None
            del_link_ids = [l.id for l in adj_links]
        else:
            # update existing adjacent links
            if adj_links:
                if len(adj_links) > 1:
                    replacement_node = 'Junction'
                    lname = ' + '.join([l.name for l in adj_links])
                    node_name = '{} {}'.format(lname, replacement_node)
                elif adj_links[0].node_1_id == node_id:
                    replacement_node = 'Inflow'
                    lname = adj_links[0].name
                    node_name = '{} {}'.format(lname, replacement_node)
                else:
                    replacement_node = 'Outflow'
                    lname = adj_links[0].name
                    node_name = '{} {}'.format(lname, replacement_node)
                x, y = [float(i) for i in gj['geometry']['coordinates']]
                node = self.make_generic_node(replacement_node, node_name, x, y)
                new_node = self.call('add_node', {'network_id': self.network.id,
                                                  'node': node})                
                if 'faultcode' in new_node and 'already in network' in new_node.faultstring:
                    new_node = [n for n in self.network.nodes if n.name==node_name][0]
                self.update_links(node_id, new_node.id)
            else:
                new_node = None
            del_link_ids = [] # don't delete adjacent links
            
        # purge node (adjacent links are deleted if not updated)
        self.call('purge_node', {'node_id': node_id, 'purge_data': 'Y'})        
        
        return new_node, new_link, del_link_ids
        
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
    
    def get_attrs(self):
        attrs = {}
        for t in self.template.types:
            for ta in t.typeattrs:
                attrs[ta.attr_id] = ta.copy()
        return AttrDict(attrs)
    
    def get_res_attrs(self):
        attrs = self.get_attrs()
        res_attrs = {}
        for f in self.network.nodes + self.network.links:
            ttype = [t.name for t in f.types if t.template_id==self.template.id][0]
            for ra in f.attributes:
                res_attr = {'res_name': f.name, 'res_type': ttype}
                res_attr.update(attrs[ra.attr_id])
                res_attrs[ra.id] = AttrDict(res_attr)
        return res_attrs
        
    
    def make_geojson_from_node(self, node=None):
        if 'geojson' in node.layout:
            gj = node.layout.geojson
        else:
            gj = {'type':'Feature', 'geometry': {'type': 'Point', 'coordinates': [node.x, node.y]}}
            
        # make sure properties are up-to-date
        type_id = [t.id for t in node.types \
                   if t.template_id==self.template.id][0]
        ttype = self.ttypes[type_id]        
        gj['properties'] = {'name': node.name,
                            'id': node.id,
                            'description': node.description,
                            'template_type_name': ttype.name,
                            'template_type_id': ttype.id,
                            'image': ttype.layout.image,
                            'template_name': self.template.name}
        return gj

    def make_geojson_from_link(self, link=None):
        
        if 'geojson' in link.layout:
            gj = node.layout.geojson
        else:         
            coords = get_coords(self.network.nodes)
            
            type_id = [t.id for t in link.types \
                       if t.template_id==self.template.id][0]
            ttype = self.ttypes[type_id]
    
            n1_id = link.node_1_id
            n2_id = link.node_2_id
            
            # for dash arrays, see:
            # https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/stroke-dasharray
            symbol = ttype.layout.symbol
            if symbol=='solid':
                dashArray = '1,0'
            elif symbol=='dashed':
                dashArray = '5,5'
            
            if n1_id in coords and n2_id in coords:
                gj = {'type':'Feature',
                     'geometry':{ 'type': 'LineString',
                                  'coordinates': [coords[n1_id], coords[n2_id]] },
                     'properties':{'name':link.name,
                                   'id':link.id,
                                   'node_1_id': n1_id,
                                   'node_2_id': n2_id,
                                   'description':link.description,
                                   'template_type_name':ttype.name,
                                   'template_type_id':ttype.id,
                                   'image':ttype.layout.image,
                                   'template_name':self.template.name,
                                   'color': name_to_hex(ttype.layout.colour),
                                   'weight': ttype.layout.line_weight,
                                   'opacity': 0.7, # move to CSS?
                                   'dashArray': dashArray,
                                   'lineJoin': 'round'
                                   }
                     }
            else:
                gj = None
        return gj
        
    # make geojson features
    def make_geojson_nodes(self):
        return [self.make_geojson_from_node(node) for node in self.network.nodes]

    # make geojson features
    def make_geojson_links(self):
        lines = []
        for link in self.network.links:
            line = self.make_geojson_from_link(link)
            if line is not None:
                lines.append(line)
            else:
                flash('Warning! "Link {}" appears to be invalid and was deleted.'.format(link.name), 'error')
                self.call('purge_link', {'link_id': link.id, 'purge_data': 'Y'})
        return lines
    
    # convert geoJson node to Hydra node
    def add_node_from_geojson(self, gj=None, existing_node_id=None):
        x, y = gj.geometry.coordinates
        ttype_name = gj.properties.template_type_name
        ttype_id = int(gj.properties.template_type_id)       
        
        typesummary = dict(
            name = ttype_name,
            id = ttype_id,
            template_name = self.template.name,
            template_id = self.template.id
        )
        node = dict(
            id = -1,
            name = gj.properties.name,
            description = gj.properties.description,
            x = str(x),
            y = str(y),
            types = [typesummary],
            layout = {'geojson': dict(gj)}
        )
        
        ## delete old node
        ## will be faster to get this client side from Leaflet Snap
        #old_node_id = None
        #for n in self.network.nodes:
            #if (x,y) == (float(n.x), float(n.y)):
                #old_node_id = n.id
                #break
        
        # add new node
        new_node = self.call('add_node', {'network_id': session['network_id'], 'node': node})
        
        # update existing adjacent links, if any, with new node id
        # it would be best if we could get the attached links clientside
        #if old_node_id is not None:
            #self.update_links(old_node_id, new_node.id)
            #self.call('purge_node', {'node_id': old_node_id})
        
        #return new_node, old_node_id
        return new_node
    
    def make_generic_node(self, ttype_name, node_name, x, y):
        typesummary = dict(
            name = ttype_name,
            id = self.ttype_dict[ttype_name],
            template_name = self.template.name,
            template_id = self.template.id
        )
        node = dict(
            id = None,
            name = node_name,
            description = '%s added automatically' % ttype_name,
            x = str(x),
            y = str(y),
            types = [typesummary]
        )
            
        #hydra_node = self.call('add_node',
                               #{'network_id': self.network.id,
                                #'node': node})          
        #return hydra_node
        return node
    
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
        
        nsegments = len(xys) - 1
        segments = range(nsegments)
        
        # make nodes
        nodes = []
        for i, s in enumerate(segments):
            for j, n in enumerate([1,2]):
                x, y = xys[i+j]
                if (x,y) not in nlookup:
                    if i==0 and j==0:
                        node_type = 'Inflow'
                        node_name = '{} {}'.format(lname, node_type)
                    elif s==segments[-1] and j==1:
                        node_type = 'Outflow'
                        node_name = '{} {}'.format(lname, node_type)
                    else:
                        node_type = 'Junction'
                        node_name = '{} {} ({},{})'.format(lname, node_type, x, y)
                    node = self.make_generic_node(node_type, node_name, x, y)
                    node['id'] = -len(nodes) # IDs should be unique
                    nodes.append(node)

                    nlookup[(x,y)] = None # to skip over next x, y
                    
        hnodes = self.call('add_nodes', {'network_id': self.network.id, 'nodes': nodes})
        #self.network = self.get_network(network_id=self.network.id, include_data='N')
        
        for n in hnodes:
            nlookup[(round(float(n.x),d), round(float(n.y),d))] = n.id
            
        # make links
        links = []
        for i in segments:
            node_1_id = nlookup[xys[i]]
            node_2_id = nlookup[xys[i+1]]
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
            link['id'] = -i
            links.append(link)
            
        hlinks = self.call('add_links', {'network_id': self.network.id, 'links': links})
        
        return hlinks, hnodes
    
    def load_active_study(self, load_from_hydra=True, include_data=False):
        
        study = Study.query.filter_by(hydra_user_id=session['hydra_user_id'], active=1).first()

        session['ti'] = app.config['TEMP_TI'] # get from study db
        session['tf'] = app.config['TEMP_TF'] # get from study db
        session['date_format'] = app.config['MONTH_FORMAT'] # get from study db
        session['amchart_date_format'] = app.config['AMCHART_DATE_FORMAT']
        session['timestep'] = 'MONTHLY' # get from study db - must match rrule functions
        session['hydra_datetime_format'] = app.config['HYDRA_DATETIME_FORMAT'] # get from config (can we query from HP?)

        if not study:
            session['project_id'] = None
            session['network_id'] = None
            session['template_id'] = None
            session['study_id'] = None
            session['study_name'] = None
            self.invalid_study = True

        else:
            session['project_id'] = study.project_id
            session['network_id'] = study.network_id
            session['template_id'] = study.template_id
            session['study_id'] = study.id
            session['study_name'] = study.name
            self.invalid_study = False
        
            if load_from_hydra:
            
                # get project
                
                self.project = self.get_project(study.project_id)
                if 'faultcode' in self.project:
                    self.project = None
                    session['project_id'] = None
                    self.invalid_study = True
                    
                # get network
                self.network = self.get_network(study.network_id, include_data)
                if 'faultcode' in self.network:
                    self.network = None
                    session['network_id'] = None
                    self.invalid_study = True
                    
                    # get scenarios
                    #scenarios = self.network.scenarios
                
                # get template
                self.template = self.get_template(study.template_id)
                if 'faultstring' in self.template:
                    self.template = None
                    self.ttypes = None
                    session['template_id'] = None
                    self.invalid_study = True
                
                else:
                    self.ttypes = {}
                    self.ttype_dict = {}
                    for ttype in self.template.types:
                        self.ttypes[ttype.id] = ttype
                        self.ttype_dict[ttype.name] = ttype.id 
                        
                # delete this once concept of studies is fully developed
                if not self.invalid_study:
                    session['study_name'] = '{}'.format(self.network.name)
                else:
                    session['study_name'] = None
                    session['study_id'] = None
    
class JSONObject(dict):
    def __init__(self, obj_dict):
        for k, v in obj_dict.items():
            self[k] = v
            setattr(self, k, v)                            
            
def make_connection(login=False):
        
    conn = connection(url=session['hydra_url'],
                      session_id=session['hydra_sessionid'])
    if login:
        
        ping = conn.call('get_username', {'uid': session['hydra_userid']})
        
        if 'faultcode' in ping and ping.faultcode == 'No Session':
            conn = connection(url=session['hydra_url'])
            # NOT SECURE IN TRANSMISSION
            conn.login(username=session['hydra_username'],
                       password=decrypt(session['hydra_password'],
                                        app.config['SECRET_ENCRYPT_KEY']))
            session['hydra_sessionid'] = conn.session_id
            update_hydrauser(db=db, hydra_user_id=session['hydra_user_id'], hydra_sessionid=conn.session_id)
    
    return conn

def save_data(conn, old_data_type, cur_data_type, res_attr, res_attr_data, new_value,
              metadata, scen_id):

    if cur_data_type == 'function':
        new_data_type = 'timeseries'
        metadata['function'] = new_value
        new_value = json.dumps(empty_hydra_timeseries())
    else:
        new_data_type = cur_data_type
        metadata.pop('function', None)
        

    ##has the data type changed? - obsolete
    #if new_data_type != old_data_type:
        ## 1. copy old typeattr:
        #old_typeattr = {'attr_id': res_attr['attr_id'],
                        #'type_id': res_attr['type_id']}
        ## 2. delete the old typeattr
        #result = conn.call('delete_typeattr', {'typeattr': old_typeattr})
        ## 3. update the old typeattr with the new data type
        #new_typeattr = old_typeattr
        #new_typeattr['attr_is_var'] = 'N'
        #new_typeattr['data_type'] = new_data_type
        #new_typeattr['unit'] = res_attr['unit']
        ## 3. add the new typeattr
        #result = conn.call('add_typeattr', {'typeattr': new_typeattr})
        
    #if res_attr_data is None: # add a new dataset
        
    # let's just try to add the new dataset directly
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
            
    # NB: this has presented a problem in the past, particularly if there is already
    # an existing dataset with the same value. In that case, we should create a new dataset instead.
    #else: # just update the existing dataset
        #dataset = res_attr_data['value']
        #dataset['type'] = new_data_type
        #dataset['value'] = new_value
        #dataset['metadata'] = json.dumps(metadata)
        
        #result = conn.call('update_dataset', {'dataset': dataset})
        
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
    hydraurl = HydraUrl.query.filter(HydraUrl.url == hydra_url).first()

    if hydraurl is None: # this should be done via manage.py, not here
        hydraurl = HydraUrl(url=hydra_url)
        db.session.add(hydraurl)
        db.session.commit()

        hydraurl = HydraUrl.query.filter(HydraUrl.url == hydra_url).first()

    # create new Hydra user account
    hydra_user_pw_encrypted = encrypt(hydra_user_password, encrypt_key)        
    conn = connection(url=hydra_url)
    conn.login(username=hydra_admin_username, # UNSECURE TRANSMISSION!
               password=hydra_admin_password) 
    hydra_user = conn.call('get_user_by_name', {'username':hydra_user_username})
    hydrauser = False
    if hydra_user:
        conn.call('update_user_password', {'user_id': hydra_user.id, 'new_password': hydra_user_password})
        
        hydrauser = HydraUser.query.filter(HydraUser.hydra_username == hydra_user.username).first()
        if hydrauser: # update hydrauser record
            hydrauser.hydra_userid = hydra_user.id
            hydrauser.hydra_password = hydra_user_pw_encrypted

    else:
        hydra_user = conn.call('add_user', {'user': {'username': hydra_user_username, 'password': hydra_user_password}})

    # add hydra user & session information to database
    if not hydrauser:
        hydrauser = HydraUser(
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

def update_hydrauser(db=None,
                     hydra_user_id=None,
                     **kwargs):
    hydrauser = HydraUser.query.filter(HydraUser.id == hydra_user_id).first()
    for kw in kwargs:
        exec('hydrauser.{} = "{}"'.format(kw, kwargs[kw]))
    db.session.commit()

def load_hydrauser():

    hydrauser = HydraUser.query.filter(HydraUser.user_id==current_user.id).first()
    if not hydrauser: # somehow the hydrauser record was not created
        return False # unsuccessful
    
    else:
        hydraurl = HydraUrl.query.filter(HydraUrl.id==hydrauser.hydra_url_id).first()
    
        session['hydra_user_id'] = hydrauser.id
        session['hydra_url'] = hydraurl.url
        session['hydra_userid'] = hydrauser.hydra_userid
        session['hydra_username'] = hydrauser.hydra_username
        session['hydra_password'] = hydrauser.hydra_password # it's encrypted
        session['hydra_sessionid'] = hydrauser.hydra_sessionid
        return True

def activate_study(db, **kwargs):
    
    # deactivate other studies
    Study.query.filter(Study.hydra_user_id == session['hydra_user_id']).update({'active': False})
    db.session.commit()
    
    hydra_user_id = kwargs['hydra_user_id']
    project_id = kwargs['project_id']
    network_id = kwargs['network_id']
    template_id = kwargs['template_id']
    
    # activate current study
    if 'study_id' in kwargs:
        study = Study.query.filter(Study.id == kwargs['study_id']).first()
    else:
        study = Study.query.filter(Study.hydra_user_id==hydra_user_id) \
                                .filter(Study.network_id==network_id) \
                                .filter(Study.template_id==template_id) \
                                .first()
        
    if study is None: # somehow a study was not created for this network
        study = add_study(db, kwargs['study_name'], hydra_user_id, project_id, network_id, template_id)
    
    else:
        study.active = True
        db.session.commit()
    
    return study

def add_study(db, name, hydra_user_id, project_id, network_id, template_id, activate=True):

    study = Study()
    study.name = name
    study.hydra_user_id = hydra_user_id
    study.project_id = project_id
    study.network_id = network_id
    study.template_id = template_id
    study.active = 0
    db.session.add(study)
    db.session.commit()
    if activate:
        Study.query.filter(Study.hydra_user_id == hydra_user_id).update({'active': False})
        db.session.commit()        
    return study

def add_chart(db, study_id, name, description, thumbnail, filters, setup):
    
    chart = Chart()
    chart.study_id = study_id
    chart.name = name
    chart.description = description
    chart.thumbnail = thumbnail
    chart.filters = filters
    chart.setup = setup
    
    db.session.add(chart)
    db.session.commit()
    
    return 0

def get_study_charts(study_id):
    charts = Chart.query.filter(Chart.study_id==study_id)
    return charts

def get_study_chart(study_id, chart_id):
    chart = Chart.query.filter_by(study_id=study_id, id=chart_id).first()
    return chart
    
def get_study_chart_names(study_id):
    charts = get_study_charts(study_id)
    return [chart.name for chart in charts]
    
def delete_study_chart(db, study_id, chart_id):
    try:
        Chart.query.filter_by(study_id=study_id, id=chart_id).delete()
        db.session.commit()
        return 1
    except:
        return -1

#reverse pivot input setups

def add_input_setup(db, study_id, name, description, filters, setup):
    
    pinput = InputSetup()
    pinput.study_id = study_id
    pinput.name = name
    pinput.description = description
    pinput.filters = filters
    pinput.setup = setup
    
    db.session.add(pinput)
    db.session.commit()
    
    return pinput.id

def get_input_setups(study_id):
    setups = InputSetup.query.filter_by(study_id=study_id)
    return {setup.id: setup.name for setup in setups}

def get_input_setup(study_id, setup_id):
    input_setup = InputSetup.query.filter_by(study_id=study_id, id=setup_id).first()
    return input_setup

def delete_input_setup(db, study_id, chart_id):
    try:
        InputSetup.query.filter_by(study_id=study_id, id=chart_id).delete()
        db.session.commit()
        return 1
    except:
        return -1
    