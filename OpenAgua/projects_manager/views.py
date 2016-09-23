from flask import render_template, redirect, url_for, request, session, json, jsonify
from flask_security import login_required, current_user

from ..connection import make_connection, load_hydrauser, add_hydrastudy, \
     activate_study

# import blueprint definition
from . import projects_manager
from OpenAgua import app, db

@projects_manager.route('/manage')
@login_required
def manage():
    load_hydrauser() # do this at the top of every page
    conn = make_connection()
    conn.load_active_study()
    
    # get the list of project names, and network names for the test project
    projects = conn.call('get_projects', {'user_id': session['hydra_userid']})
    networks = conn.call('get_networks', {'project_id': session['project_id']})
    
    return render_template('projects_manager.html',
                           projects=projects,
                           networks=networks)

@projects_manager.route('/manage/templates')
@login_required
def manage_templates():
    conn = make_connection()
    
    # get list of all templates
    templates = conn.call('get_templates', {})
    
    return render_template('templates_manager.html',
                           templates=templates)

@projects_manager.route('/_edit_schematic')
@login_required
def edit_schematic():
    conn = make_connection()
    network_id = int(request.args.get('network_id'))
    activate_study(db, session['hydrauser_id'], session['project_id'],
                   network_id)
    conn.load_active_study()
    if conn.invalid_study:
        # create a new study with the just-selected network + default scenario
        templates = conn.call('get_templates', {})
        template = [t for t in templates if t.name == 'OpenAgua'][0]
        add_hydrastudy(db,
                       user_id = current_user.id,
                       hydrauser_id = session['hydrauser_id'],
                       project_id = session['project_id'],
                       network_id = network_id,
                       template_id = template.id,
                       active = 1
                       )
        activate_study(db, session['hydrauser_id'], session['project_id'],
                       network_id)
        conn.load_active_study()    
    
    return jsonify(resp=0)

@projects_manager.route('/_add_project')
@login_required
def add_project():
    conn = make_connection()
    
    projects = conn.call('get_projects', {'user_id':session['hydra_user_id']})
    project_names = [project.name for project in projects]
    activate = request.args.get('activate')
    proj = request.args.get('proj')
    proj = json.loads(proj)
    if proj['name'] in project_names:
        status_code = -1 # name already exists
    else:
        project = conn.call('add_project', {'project':proj})
        status_code = 1
    
    return jsonify(result={'status_code': status_code})


@projects_manager.route('/_add_network', methods=['GET', 'POST'])
@login_required
def add_network():
    conn = make_connection()

    networks = conn.call('get_networks',
                         {'project_id': session['project_id'],
                          'include_data': 'N'})
    network_names = [network.name for network in networks]
    
    # add network
    new_net = request.args.get('net')
    new_net = json.loads(new_net)
    tpl_id = session['template_id']
    if new_net['name'] in network_names:
        return jsonify(result={'status_code': -1})
    
    new_net['project_id'] = session['project_id']
    network = conn.call('add_network', {'net':new_net})

    # add the template
    conn.call('apply_template_to_network',
              {'template_id': tpl_id, 'network_id': network.id})
    
    # add a default scenario (similar to Hydra Modeller)
    scenario = dict(
        name = 'Baseline',
        description = 'Default OpenAgua scenario'
    )

    result = conn.call('add_scenario',
                       {'network_id': network.id, 'scen': scenario})
    
    # create a default study consisting of the project, network, and scenario
    add_hydrastudy(db,
        user_id = current_user.id,
        hydrauser_id = session['hydrauser_id'],
        project_id = session['project_id'],
        network_id = network.id,
        template_id = session['template_id'],
        active = 1
    )
    
    conn.load_active_study()
        
    return jsonify(result={'status_code': 1})


@projects_manager.route('/_purge_project')
@login_required
def purge_project():
    conn = make_connection()
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

@projects_manager.route('/_upgrade_template')
@login_required
def upgrade_template():
    conn = make_connection()
    
    network_id = int(request.args.get('network_id'))
    template_id = int(request.args.get('template_id'))
    
    # simply detach existing template and re-attach
    resp = conn.call('remove_template_from_network',
                     {'network_id': network_id,
                      'template_id': template_id,
                      'remove_attrs': 'N'})
    
    resp = conn.call('apply_template_to_network',
                      {'template_id': template_id,
                       'network_id': network_id})
    
    # attach new template
    
    if resp=='OK':
        status_code = 1        
    else:
        status_code = -1
    return jsonify(status=status_code)

@projects_manager.route('/_update_template')
@login_required
def update_template():
    import zipfile
    
    conn = make_connection()
    
    template_id = int(request.args.get('template_id'))
    
    # upload the new template    
    zf = zipfile.ZipFile(app.config['TEMPLATE_FILE'])
    template_xml = zf.read('OpenAgua/template/template.xml').decode('utf-8')
    resp = conn.call('upload_template_xml',
                            {'template_xml': template_xml}) 
    
    if 'faultcode' not in resp:
        status_code = 1        
    else:
        status_code = -1
    return jsonify(status=status_code)


@projects_manager.route('/_get_templates_for_network')
@login_required
def get_templates_for_network():
    conn = make_connection()
    network_id = request.args.get('network_id')
    if network_id is not None:
        network_id = int(network_id)
        net = conn.call('get_network', {'network_id': network_id})
        tpls = conn.call('get_templates', {})
        
        net_tpl_ids = [t.template_id for t in net.types]
        net_tpls = [tpl for tpl in tpls if tpl.id in net_tpl_ids]
    else:
        net_tpls = []
    return jsonify(templates=net_tpls)


@projects_manager.route('/_hydra_call', methods=['GET', 'POST'])
@login_required
def hydra_call():
    conn = make_connection()
    
    func = request.args.get('func')
    args = request.args.get('args')
    args = json.loads(args)
    result = conn.call(func, args)
    
    return jsonify(result=result)