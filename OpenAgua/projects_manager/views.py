from flask import render_template, request, session, json, jsonify
from flask_security import login_required

from ..connection import make_connection, load_hydrauser

# import blueprint definition
from . import projects_manager
from OpenAgua import app

@projects_manager.route('/manage')
@login_required
def manage():
    load_hydrauser() # do this at the top of every page
    conn = make_connection()
    conn.load_active_study()
    
    session['project_id'] = conn.project.id
    session['network_id'] = conn.network.id
    
    # get the list of project names, and network names for the test project
    projects = conn.call('get_projects', {'user_id': session['hydra_userid']})
    networks = conn.call('get_networks', {'project_id': conn.project.id})
    
    # get list of all templates
    templates = conn.call('get_templates',{})
    
    return render_template('projects_manager.html',
                           projects=projects,
                           networks=networks,
                           templates=templates)

@projects_manager.route('/_add_project')
@login_required
def add_project():
    conn = make_connection(session, include_network=False,
                           include_template=False)
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
    
    # connect & get networks
    conn = make_connection()
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
            description = 'Default OpenAgua scenario'
        )

        result = conn.call('add_scenario',
                           {'network_id': network.id, 'scen': scenario})
        #network = conn.call('get_network', {'network_id': network.id})
            
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
    
    zf = zipfile.ZipFile(app.config['TEMPLATE_FILE'])
    template_xml = zf.read('OpenAgua/template/template.xml')
    resp = conn.call('upload_template_xml',
                            {'template_xml': template_xml.decode()}) 
    
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
    
    if func == 'delete_template':
        session['template_id'] = None
        session['template_name'] = None
    
    return jsonify(result=result)