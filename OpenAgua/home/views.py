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
    if current_user.has_role('pro_user'):
        # user will create their own project, but we still need to create a default study
        default_project_id = -1
    else:
        conn = make_connection(login=True)

        project_name = current_user.email
        project_description = 'Default project created for {} {} ({})' \
            .format(current_user.firstname, current_user.lastname, current_user.email)
        
        default_projects = conn.call('get_projects', {'user_id': session['hydra_userid']})
        default_project = default_projects[0]
        if not default_project:
            default_project = conn.add_default_project(project_name, project_description)
        default_project_id = default_project.id
    
    default_network_id = -1
    templates = conn.call('get_templates', {})
    default_template_id = [tpl.id for tpl in templates if tpl.name == app.config['DEFAULT_HYDRA_TEMPLATE']][0]
        
    add_study(db=db,
              name='Default study for {}'.format(current_user.email),
              user_id=current_user.id,
              hydrauser_id=session['hydrauser_id'],
              project_id=default_project_id,
              network_id=default_network_id,
              template_id=default_template_id,
              activate=True)
        
    flash('Account created!')
    return(redirect(url_for('home.home_main')))

@home.route('/home')
@login_required
def home_main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study(load_from_hydra=False)
    if session['project_id'] is None:
        projects = conn.call('get_projects', {'user_id': session['hydra_userid']})
        session['project_id'] = projects[0].id
    
    if current_user.has_role('pro_user') or current_user.has_role('superuser'):
        user_level = "pro"
    else:
        user_level = "basic"
    
    return render_template('home.html', user_level=user_level)

@home.route('/manage/templates')
@login_required
def manage_templates():
    conn = make_connection()
    
    # get list of all templates
    templates = conn.call('get_templates', {})
    
    return render_template('templates_manager.html',
                           templates=templates)

@home.route('/_load_study')
@login_required
def load_study():
    conn = make_connection()
    network_id = int(request.args.get('network_id'))
    activate_study(db, session['hydrauser_id'], session['project_id'],
                   network_id)
    conn.load_active_study()
    if conn.invalid_study:
        # create a new study with the just-selected network + default scenario
        templates = conn.call('get_templates', {})
        template = [t for t in templates if t.name == 'OpenAgua'][0]
        add_study(db,
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

@home.route('/_add_project')
@login_required
def add_project():
    conn = make_connection()
    
    projects = conn.call('get_projects', {'user_id':session['hydra_userid']})
    project_names = [project.name for project in projects]
    activate = request.args.get('activate')
    proj = request.args.get('proj')
    proj = json.loads(proj)
    if proj['name'] in project_names:
        status_code = -1 # name already exists
    else:
        project = conn.call('add_project', {'project':proj})
        status_code = 1
    
    return jsonify(status_code=status_code)


@home.route('/_add_network', methods=['GET', 'POST'])
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
    tpl_id = int(request.args.get('tpl_id'))
    if new_net['name'] in network_names:
        return jsonify(status_code -1)
    
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


@home.route('/manage/templates/_upload', methods=['GET', 'POST'])
@login_required
def upload_template():

    if request.method == 'POST' and 'template' in request.files:
        
        conn = make_connection()
        
        template = request.files['template']
        
        filename = templates.save(template)

        zf  = zipfile.ZipFile(template.stream)
        
        # load template
        template_xml_path = zf.namelist()[0]
        template_xml = zf.read(template_xml_path).decode('utf-8')
        resp = conn.call('upload_template_xml',
                                {'template_xml': template_xml}) 
        zf.extractall(path=app.config['UPLOADED_TEMPLATES_DEST'])
        
        template_name = template_xml_path.split('/')[0]
        flash('Template %s uploaded successfully' % template_name, category='info')
    else:
        flash('Something went wrong.')
        
    return redirect(url_for('home.manage_templates'))
        
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