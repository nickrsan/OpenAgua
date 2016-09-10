from flask import render_template, request, session, redirect, url_for
from flask_user import login_required
from ..connection import connection

# import blueprint definition
from . import user_home
from OpenAgua import app

@user_home.route('/home')
@login_required
def home():

    session['url'] = app.config['HYDRA_URL']
    session['hydra_username'] = app.config['HYDRA_USERNAME']
    session['hydra_password'] = app.config['HYDRA_PASSWORD']    

    # connect to hydra (login if we don't already have a session ID)
    if 'session_id' in session:
        conn = connection(url=session['url'], session_id=session['session_id'])
    else:
        conn = connection(url=session['url'])
    
    # this makes sure we are logged in, in case there is a leftover session_id
    # in the Flask session. We shouldn't get here though.
    conn.login(username = session['hydra_username'], password = session['hydra_password'])    
    session['session_id'] = conn.session_id
    session['hydra_user_id'] = conn.user_id

    # add recent project/network/template to session (to be loaded from user data in the future)
    session['project_name'] = app.config['HYDRA_PROJECT_NAME']
    session['network_name'] = app.config['HYDRA_NETWORK_NAME'] 
    session['template_name'] = app.config['HYDRA_TEMPLATE_NAME']
    session['project_id'] = -1
    session['network_id'] = -1
    session['template_id'] = -1
    
    # load / create project
    projects = conn.call('get_projects', {})
    if session['project_name'] in [proj.name for proj in projects]:
        project = conn.get_project_by_name(session['project_name'])
        session['project_id'] = project.id
    else:
        return redirect(url_for('projects_manager.manage')) 
    
    # load / activate network
    networks = conn.call('get_networks',{'project_id':project.id})
    if session['network_name'] in [net.name for net in networks]:
        network = conn.get_network_by_name(session['project_id'], session['network_name'])
        session['network_id'] = network.id
    else:
        return redirect(url_for('projects_manager.manage'))    

    # load / activate template (temporary fix)
    templates = conn.call('get_templates',{})
    if len(templates)==0:
        return redirect(url_for('projects_manager.manage')) 
    
    template_names = [t.name for t in templates]    
    if session['template_name'] not in template_names:
        return redirect(url_for('projects_manager.manage'))
    
    session['template_id'] = [t.id for t in templates if t.name==session['template_name']][0]
    
    session['appname'] = 'pyomo_network_lp'

    # if we've made it this far, let's send the user directly to the overview of
    # their most recent project, pending more interesting stuff
    return redirect(url_for('main_overview.overview'))
    #return render_template('user_home.html')

# Load projects
# in the future, we can (optionally) store the Hydra session ID with the user account
# i.e., give the user an option to auto-load last-used project.
@user_home.route('/_load_recent')
def load_recent():
    
    # load / create project
    #project = conn.get_project_by_name(session['project_name'])
    #if 'id' in project.keys():
        #session['project_id'] = project.id
    #else:
        #return redirect(url_for('projects_manager.manage')) 
    
    ## load / activate network
    #network = conn.get_network_by_name(session['project_id'], session['network_name'])
    #if 'id' in network.keys():
        #session['network_id'] = network.id
    #else:
        #return redirect(url_for('projects_manager.manage'))    

    ## load / activate template (temporary fix)
    #templates = conn.call('get_templates',{})
    #if len(templates)==0:
        #return redirect(url_for('projects_manager.manage')) 
    
    #template_names = [t.name for t in templates]    
    #if session['template_name'] not in template_names:
        #return redirect(url_for('projects_manager.manage'))    
    
    return redirect(url_for('main_overview.overview'))