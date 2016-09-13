from flask import render_template, request, session, redirect, url_for
from flask_user import login_required, current_user
#from simplecrypt import encrypt, decrypt
#from Crypto.Cipher import AES
from cryptography.fernet import Fernet
from ..connection import connection

# import blueprint definition
from . import user_home
from OpenAgua import app, db, user_manager
from OpenAgua.models import User, HydraUrl, HydraUser

@user_home.route('/home')
@login_required
def home():

    if current_user.new_user:
        hydra_url = app.config['HYDRA_URL']
        hydraurl = HydraUrl.query \
            .filter(HydraUrl.hydra_url == hydra_url).first()

        if hydraurl is None: # this should be done via manage.py, not here
            hydraurl = HydraUrl(hydra_url=hydra_url)
            db.session.add(hydraurl)
            db.session.commit()

        hydraurl = HydraUrl.query \
            .filter(HydraUrl.hydra_url==hydra_url).first()
        
        # create new Hydra user account
        hydra_user_pw = 'password' # get from user later
        #obj = AES.new(app.config['HYDRA_ENCRYPT_PASSWORD'],
                      #AES.MODE_CBC,
                      #app.config['SECRET_ENCRYPT_KEY'])
        #hydra_user_pw_encrypted = obj.encrypt(hydra_user_pw)
        f = Fernet(app.config['SECRET_ENCRYPT_KEY'])
        hydra_user_pw_encrypted = f.encrypt(b"my deep dark secret")        
        conn = connection(url=hydra_url)
        # IMPORTANT: this is transmitted unencrypted. Need to secure this.
        conn = connection(url=app.config['HYDRA_URL'])
        conn.login(username=app.config['HYDRA_ROOT_USERNAME'],
                   password=app.config['HYDRA_ROOT_PASSWORD'])
        hydra_user = conn.call('get_user_by_name',
                               {'username':current_user.username})
        if not hydra_user:
            hydra_user = conn.call('add_user',
                                   {'user': {'username': current_user.username,
                                             'password': hydra_user_pw}})
            
        conn.login(username=current_user.username,
                   password=hydra_user_pw)
        session['hydra_session_id'] = conn.session_id
        
        # add hydra user information to database
        #hydrauser = HydraUser( \
            #user_id = current_user.id,
            #hydra_url_id = hydraurl.id,
            #hydra_userid = hydra_user.id,
            #hydra_username = hydra_user.username,
            #hydra_password = hydra_user_pw_encrypted,
            #hydra_sessionid = conn.session_id
        #)
        #db.session.add(hydrauser)
        #db.session.commit()
        
        user = User.query \
            .filter(User.username == current_user.username).first()  
        user.new_user = False
        db.session.commit()
    
    # get current hydra user
    hydrauser = HydraUser.query \
        .filter(HydraUser.user_id == current_user.id).first()
    hydraurl = HydraUrl.query \
                .filter(HydraUrl.id == hydrauser.hydra_url_id).first()    
    
    conn = connection(url=hydraurl.hydra_url,
                      session_id=hydrauser.hydra_sessionid)
    if not conn:
        # shouldn't get here since sessionid should be permanent
        f = Fernet(app.config['SECRET_ENCRYPT_KEY'])
        hydra_user_pw = F.decrypt(hydra_user_pw_encrypted)
        conn = connection(url=session['url'])
        conn.login(username=current_user.hydra_username, password=hydra_user_pw)
        session['hydra_session_id']=conn.session_id    
        hydra_user_pw = None # just to be safe
    
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