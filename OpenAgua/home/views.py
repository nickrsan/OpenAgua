from os.path import join
import zipfile

from flask import render_template, redirect, url_for, request, session, json, jsonify, flash
from flask_security import login_required, current_user

from flask_uploads import UploadSet, configure_uploads, ARCHIVES

from ..connection import make_connection, create_hydrauser, load_hydrauser, add_study,  activate_study

# import blueprint definition
from . import home
from OpenAgua import app, db

templates = UploadSet('templates', ARCHIVES)
configure_uploads(app, templates)

@home.route('/_account_setup')
@login_required
def account_setup():

    create_hydrauser(db=db,
                     user_id=current_user.id,
                     hydra_url=app.config['HYDRA_URL'],
                     encrypt_key=app.config['SECRET_ENCRYPT_KEY'],
                     hydra_admin_username=app.config['HYDRA_ROOT_USERNAME'],
                     hydra_admin_password=app.config['HYDRA_ROOT_PASSWORD'],
                     hydra_user_username=current_user.email,
                     hydra_user_password='password') # to be set by user    
    load_hydrauser()
        
    return(redirect(url_for('home.home_main')))

@home.route('/home')
@login_required
def home_main():

    if not load_hydrauser():
        return redirect(url_for('home.account_setup'))
    
    conn = make_connection(login=True)    
          
    if current_user.has_role('pro_user') or current_user.has_role('superuser'):
        session['user_level'] = "pro" # we should move this to load_hydrauser
    else:
        session['user_level'] = "basic"    

    conn.load_active_study(load_from_hydra=False)
    session['study_name'] = None # turn this off for the home page
    
    # conditional actions depending on whether or not an active study exists
    if session['project_id'] is None:
        
        # the following should probably be moved to a function
        projects = conn.call('get_projects', {'user_id': session['hydra_userid']})
        if projects:
            session['project_id'] = projects[0].id
        elif session['user_level'] == "basic": # shouldn't get here
            default_project = conn.add_default_project()
            session['project_id'] = default_project.id
        
    if session['template_id'] is None:
        templates = conn.call('get_templates', {})
        default_template_id = [tpl.id for tpl in templates if tpl.name == app.config['DEFAULT_HYDRA_TEMPLATE']]
        if not default_template_id:
            if current_user.has_role('superuser'):
                flash('Default template does not exist. Please upload it!', category='error')
                return redirect(url_for('manager.manage_templates'))
            else:
                flash('Default template does not exist. Please contact support: admin@openagua.org', category='error')
                return redirect('/logout')
        else:
            session['template_id'] = default_template_id[0]        
    
    return render_template('home.html')

@home.route('/_load_study', methods['GET', 'POST'])
@login_required
def load_study():
    
    if request.method == 'POST':
        
        conn = make_connection()
        network_id = request.json['network_id']
        project_id = request.json['project_id']
        activate_study(db, session['hydrauser_id'], session['project_id'], network_id)
        conn.load_active_study()
        if conn.invalid_study:
            # create a new study with the just-selected network + default scenario
            network = conn.get_network(network_id=network_id)
            add_study(db,
                      name = 'Base study for {}'.format(network.name),
                      user_id = current_user.id,
                      hydrauser_id = session['hydrauser_id'],
                      project_id = project_id,
                      network_id = network_id,
                      template_id = session['template_id'],
                      activate = True)
            conn.load_active_study()    
        
        return jsonify(resp=0)
    
    redirect(url_for('home.home_main')) 

@home.route('/_add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    
    if request.method == 'POST':
        conn = make_connection()
        
        projects = conn.call('get_projects', {'user_id':session['hydra_userid']})
        project_names = [project.name for project in projects]
        proj = request.json['proj']
        if proj['name'] in project_names:
            status_code = -1 # name already exists
            project_id = None
        else:
            project = conn.call('add_project', {'project':proj})
            status_code = 1
            project_id = project.id
        
        return jsonify(status_code=status_code, new_project_id=project_id)
    
    redirect(url_for('home.home_main')) 


@home.route('/_add_network', methods=['GET', 'POST'])
@login_required
def add_network():
    
    if request.method == 'POST':
    
        conn = make_connection()
        
        # add network
        proj_id = request.json['proj_id']
        new_net = request.json['net']
        tpl_id = request.json['tpl_id']
        
        network = conn.call('add_network', {'net':new_net})
    
        # add the template
        conn.call('apply_template_to_network', {'template_id': tpl_id, 'network_id': network.id})
        
        # add a default scenario (similar to Hydra Modeller)
        scenario = dict(
            name = 'Baseline',
            description = 'Default OpenAgua scenario'
        )
    
        result = conn.call('add_scenario', {'network_id': network.id, 'scen': scenario})
        
        # create a default study consisting of the project, network, and scenario
        add_study(db = db,
                  name = 'Base study for {}'.format(network.name),
                  user_id = current_user.id,
                  hydrauser_id = session['hydrauser_id'],
                  project_id = session['project_id'],
                  network_id = network.id,
                  template_id = session['template_id'],
                  activate = True
              )
        
        conn.load_active_study()
            
        return jsonify(status_code=1)
    
    redirect(url_for('home.home_main'))


@home.route('/_purge_project')
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

@home.route('/_upgrade_template')
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

        
@home.route('/_get_templates_for_network')
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

@home.route('/_hydra_call', methods=['GET', 'POST'])
@login_required
def hydra_call():
    conn = make_connection()
    
    func = request.args.get('func')
    args = request.args.get('args')
    args = json.loads(args)
    result = conn.call(func, args)
    
    return jsonify(result=result)