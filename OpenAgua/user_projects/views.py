from __future__ import print_function
import os
from flask import render_template, request, session, json, jsonify
import zipfile
from ..connection import connection
from ..conversions import *

from sys import stderr

# import blueprint definition
from . import user_projects

here = os.path.dirname(os.path.abspath(__file__))

@user_projects.route('/projects')
@login_required
def project_settings():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    # get the list of project names and network names for the test project ('Monterrey')
    projects = conn.call('get_projects',{'user_id':session['user_id']})
    project_names = [project.name for project in projects]
    if session['project_name'] in project_names:
        if 'project_id' not in session:
            project = conn.get_project_by_name(project_name=session['project_name'])
            session['project_id'] = project.id
        networks = conn.call('get_networks',{'project_id':session['project_id'],'include_data':'N'})
        network_names = [network.name for network in networks]
    else:
        network_names = []
        
    # get list of all templates
    templates = conn.call('get_templates',{})
    template_names = [t.name for t in templates]
    
    if 'WEAP' not in template_names:
        zf = zipfile.ZipFile(os.path.join(here, 'static/hydra_templates/WEAP.zip'))
        template_xml = zf.read('WEAP/template/template.xml')
        conn.call('upload_template_xml', {'template_xml':template_xml})
        templates = conn.call('get_templates',{})
    
    return render_template('projects_manager.html',
                           project_names=project_names,
                           network_names=network_names,
                           templates=templates)

@user_projects.route('/_add_project')
def add_project():
    conn = connection(url=session['url'], session_id=session['session_id'])
    projects = conn.call('get_projects', {'user_id':session['user_id']})
    project_names = [project.name for project in projects]
    #activate_proj = request.args.get('activate_project')
    activate_proj = True
    proj = request.args.get('proj')
    proj = json.loads(proj)
    if proj['name'] in project_names:
        return jsonify(result={'status_code': -1})
    
    project = conn.call('add_project', {'project':proj})
    if activate_proj:
        session['project_name'] = project.name
        session['project_id'] = project.id
        return jsonify(result={'status_code': 1})

@user_projects.route('/_add_network', methods=['GET', 'POST'])
def add_network():
    
    # connect & get networks
    conn = connection(url=session['url'], session_id=session['session_id'])
    networks = conn.call('get_networks', {'project_id':session['project_id'], 'include_data':'N'})
    network_names = [network.name for network in networks]
    #activate_net = request.args.get('activate_network')
    activate_net = True
    
    # add network
    new_net = request.args.get('net')
    new_net = json.loads(new_net)
    tpl_id = int(request.args.get('tpl_id'))
    if new_net['name'] in network_names:
        return jsonify(result={status_code: -1})
    else:
        new_net['project_id'] = session['project_id']
        network = conn.call('add_network', {'net':new_net})

        # add the template
        conn.call('apply_template_to_network', {'template_id': tpl_id, 'network_id': network.id})
        
        # add a default scenario
        #scen = {'name':'Baseline', 'return_summary':'N'}
        #conn.call('add_scenario', {'network_id':network.id, 'scen':scen})
        #network = conn.call('get_network', {'network_id':network.id})
        #print(network, file=stderr)
        
        if activate_net:
            session['network_name'] = network.name
            session['network_id'] = network.id
            
        return jsonify(result={'status_code': 1})
