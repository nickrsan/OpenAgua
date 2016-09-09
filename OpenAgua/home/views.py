from flask import render_template, request, session, redirect, url_for
from flask_user import login_required
from ..connection import connection

# import blueprint definition
from . import user_home
import OpenAgua

@user_home.route('/home')
@login_required
def home():

    session['url'] = OpenAgua.app.config['HYDRA_URL']
    session['hydra_username'] = OpenAgua.app.config['HYDRA_USERNAME']
    session['hydra_password'] = OpenAgua.app.config['HYDRA_PASSWORD']    

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
    session['project_name'] = OpenAgua.app.config['HYDRA_PROJECT_NAME']
    session['network_name'] = OpenAgua.app.config['HYDRA_NETWORK_NAME'] 
    session['template_name'] = OpenAgua.app.config['HYDRA_TEMPLATE_NAME']
    
    # load / create project
    project = conn.get_project_by_name(session['project_name'])
    if 'id' in project.keys():
        session['project_id'] = project.id
    else:
        return redirect(url_for('projects_manager.projects_manager')) 
    
    # load / activate network
    network = conn.get_network_by_name(session['project_id'], session['network_name'])
    if 'id' in network.keys():
        session['network_id'] = network.id
    else:
        return redirect(url_for('projects_manager.projects_manager'))    

    # load / activate template (temporary fix)
    templates = conn.call('get_templates',{})
    if len(templates)==0:
        return redirect(url_for('projects_manager.projects_manager')) 
    
    template_names = [t.name for t in templates]    
    if session['template_name'] not in template_names:
        return redirect(url_for('projects_manager.projects_manager'))
    
    session['template_id'] = [t.id for t in templates if t.name==session['template_name']][0]
    
    session['appname'] = 'pyomo_network_lp'

    # if we've made it this far, let's send the user directly to the overview of
    # their most recent project, pending more interesting stuff
    #return render_template('home.html')
    return redirect(url_for('main_overview.overview'))

# Load projects
# in the future, we can (optionally) store the Hydra session ID with the user account
# i.e., give the user an option to auto-load last-used project.
@user_home.route('/_load_recent')
def load_recent():   
    return redirect(url_for('main_overview.overview'))