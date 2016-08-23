from __future__ import print_function
import os
from flask import render_template, request, session, json, jsonify, redirect
from flask_user import login_required
import zipfile
import datetime

from ..connection import connection
#from ..decorators import *

from sys import stderr

# import blueprint definition
from . import user_projects

here = os.path.dirname(os.path.abspath(__file__))

@user_projects.route('/projects_manager')
@login_required
def projects_manager():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    # get the list of project names and network names for the test project ('Monterrey')
    projects = conn.call('get_projects',{'user_id':session['user_id']})
    project_names = [project.name for project in projects]
    if session['project_name'] in project_names:
        project = conn.get_project_by_name(project_name=session['project_name'])
        session['project_id'] = project.id
        networks = conn.call('get_networks',{'project_id':session['project_id'],'include_data':'N'})
    else:
        networks = []
        
    # get list of all templates
    #template_id = conn.call('get_template_by_name', {'template_name':session['template_name']})
    templates = conn.call('get_templates',{})
    template_names = [t.name for t in templates]    
    
    if session['template_name'] not in template_names:
        zf = zipfile.ZipFile(os.path.join(here, 'static/hydra_templates/OpenAgua.zip'))
        template_xml = zf.read('OpenAgua/template/template.xml')
        conn.call('upload_template_xml', {'template_xml':template_xml})
        
    templates = conn.call('get_templates',{})
    template_names = [t.name for t in templates]
        
    return render_template('projects_manager.html',
                           projects=projects,
                           networks=networks,
                           templates=templates)

@user_projects.route('/_add_project')
def add_project():
    conn = connection(url=session['url'], session_id=session['session_id'])
    projects = conn.call('get_projects', {'user_id':session['user_id']})
    project_names = [project.name for project in projects]
    activate = request.args.get('activate')
    proj = request.args.get('proj')
    proj = json.loads(proj)
    if proj['name'] in project_names:
        status_code = -1 # name already exists
    project = conn.call('add_project', {'project':proj})
    status_code = 1
    print(activate, file=stderr)
    if activate:
        session['project_name'] = project.name
        session['project_id'] = project.id
        print(session['project_name'], file=stderr)
    
    return jsonify(result={'status_code': status_code})

@user_projects.route('/_add_network', methods=['GET', 'POST'])
def add_network():
    
    # connect & get networks
    conn = connection(url=session['url'], session_id=session['session_id'])
    networks = conn.call('get_networks', {'project_id':session['project_id'], 'include_data':'N'})
    network_names = [network.name for network in networks]
    #activate_net = request.args.get('activate_network')
    
    # add network
    new_net = request.args.get('net')
    new_net = json.loads(new_net)
    tpl_id = int(request.args.get('tpl_id'))
    if new_net['name'] in network_names:
        return jsonify(result={'status_code': -1})
    else:
        new_net['project_id'] = session['project_id']
        network = conn.call('add_network', {'net':new_net})

        # add the template
        conn.call('apply_template_to_network', {'template_id': tpl_id, 'network_id': network.id})
        
        # add a default scenario (similar to Hydra Modeller)
        scenario = dict(
            name = 'Baseline',
            description = 'Baseline scenario'
        )

        result = conn.call('add_scenario', {'network_id':network.id, 'scen':scenario})
        network = conn.call('get_network', {'network_id':network.id})
            
        return jsonify(result={'status_code': 1})

@user_projects.route('/_purge_project')
def purge_project():
    conn = connection(url=session['url'], session_id=session['session_id'])
    project_id = int(request.args.get('project_id'))
    
    resp = conn.call('purge_project', {'project_id':project_id})
    if resp=='OK':
        status_code = 1
        if session['project_id'] == project_id:
            session['project_name'] = None
            session['project_id'] = None        
    else:
        status_code = -1
    return jsonify(result={'status_code': status_code})

@user_projects.route('/_hydra_call', methods=['GET', 'POST'])
def hydra_call():
    conn = connection(url=session['url'], session_id=session['session_id'])
    func = request.args.get('func')
    args = request.args.get('args')
    args = json.loads(args)
    result = conn.call(func, args)
    return jsonify(result=result)