from sys import stderr
import os
import zipfile
import datetime

from flask import render_template, request, session, json, jsonify, redirect
from flask_user import login_required

from ..connection import connection

# import blueprint definition
from . import projects_manager

here = os.path.dirname(os.path.abspath(__file__))

@projects_manager.route('/projects')
@login_required
def projects():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    # get the list of project names, and network names for the test project
    projects = conn.call('get_projects',{'user_id':session['hydra_user_id']})
    project_names = [project.name for project in projects]
    if session['project_name'] in project_names:
        project = \
            conn.get_project_by_name(project_name = session['project_name'])
        session['project_id'] = project.id
        networks = conn.call('get_networks',
                             {'project_id': session['project_id'],
                              'include_data': 'N'})
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
        
    return render_template('projects.html',
                           projects=projects,
                           networks=networks,
                           templates=templates)


@projects_manager.route('/_add_project')
@login_required
def add_project():
    conn = connection(url=session['url'], session_id=session['session_id'])
    projects = conn.call('get_projects', {'user_id':session['hydra_user_id']})
    project_names = [project.name for project in projects]
    activate = request.args.get('activate')
    proj = request.args.get('proj')
    proj = json.loads(proj)
    if proj['name'] in project_names:
        status_code = -1 # name already exists
    project = conn.call('add_project', {'project':proj})
    status_code = 1
    
    if activate:
        session['project_name'] = project.name
        session['project_id'] = project.id
    
    return jsonify(result={'status_code': status_code})


@projects_manager.route('/_add_network', methods=['GET', 'POST'])
@login_required
def add_network():
    
    # connect & get networks
    conn = connection(url=session['url'], session_id=session['session_id'])
    networks = conn.call('get_networks',
                         {'project_id': session['project_id'],
                          'include_data': 'N'})
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
        conn.call('apply_template_to_network',
                  {'template_id': tpl_id, 'network_id': network.id})
        
        # add a default scenario (similar to Hydra Modeller)
        scenario = dict(
            name = 'Baseline',
            description = 'Baseline scenario'
        )

        result = conn.call('add_scenario',
                           {'network_id': network.id, 'scen': scenario})
        network = conn.call('get_network', {'network_id': network.id})
            
        return jsonify(result={'status_code': 1})


@projects_manager.route('/_purge_project')
@login_required
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


@projects_manager.route('/_get_templates_for_network')
@login_required
def get_templates_for_network():
    conn = connection(url=session['url'], session_id=session['session_id'])
    network_id = int(request.args.get('network_id'))
    
    net = conn.call('get_network', {'network_id': network_id})
    tpls = conn.call('get_templates', {})
    
    net_tpl_ids = [t.template_id for t in net.types]
    net_tpls = [tpl for tpl in tpls if tpl.id in net_tpl_ids]
    
    return jsonify(templates=net_tpls)
    
@projects_manager.route('/_delete_template')
@login_required
def delete_template():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    resp = conn.call('delete_template', {'delete_template':template_id})
    if resp=='OK':
        status_code = 1
        if session['template_id'] == template_id:
            session['template_name'] = None
            session['template_id'] = None        
    else:
        status_code = -1
    return jsonify(result={'status_code': status_code})


@projects_manager.route('/_hydra_call', methods=['GET', 'POST'])
@login_required
def hydra_call():
    conn = connection(url=session['url'], session_id=session['session_id'])
    func = request.args.get('func')
    args = request.args.get('args')
    args = json.loads(args)
    result = conn.call(func, args)
    return jsonify(result=result)