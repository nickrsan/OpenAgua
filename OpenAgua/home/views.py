from flask import render_template, request, session, redirect, url_for
from flask_user import login_required, current_user

from ..connection import make_connection, create_hydrauser, load_hydrauser
from . import user_home
from OpenAgua import app, db, user_manager
from OpenAgua.models import User, HydraUrl, HydraUser, HydraProject

@user_home.route('/home')
@login_required
def home():

    hydrauser = HydraUser.query \
        .filter(HydraUser.user_id==current_user.id).first()
    
    if not hydrauser: # we should do this after email confirmation, not here
        
        create_hydrauser(db=db,
                         user_id=current_user.id,
                         hydra_url=app.config['HYDRA_URL'],
                         encrypt_key=app.config['SECRET_ENCRYPT_KEY'],
                         hydra_admin_username=app.config['HYDRA_ROOT_USERNAME'],
                         hydra_admin_password=app.config['HYDRA_ROOT_PASSWORD'],
                         hydra_user_username=current_user.username,
                         hydra_user_password='password')
        
        # update the user new_user flag
        user = User.query \
            .filter(User.username == current_user.username).first()  
        user.new_user = False  
    
    # load hydrauser
    load_hydrauser()
    conn = make_connection(session, include_network=False, 
                          include_template=False)
    conn.load_active_study()
    
    #if not conn:
        ## shouldn't get here since sessionid should be permanent
        #f = Fernet(app.config['SECRET_ENCRYPT_KEY'])
        #hydra_user_pw = f.decrypt(hydra_user_pw_encrypted)
        #conn = connection(url=hydrauser.hydra_url)
        #conn.login(username=current_user.hydra_username, password=hydra_user_pw) 
        #session['hydra_sessionid'] = conn.session_id
        #hydra_user_pw = None # just to be safe
    
    if session['project_id'] is None \
       or session['network_id'] is None \
       or session['template_id'] is None:
        return redirect(url_for('projects_manager.manage'))

    return redirect(url_for('main_overview.overview'))
    #return render_template('user_home.html')

# Load projects
@user_home.route('/_load_recent')
def load_recent():
    return redirect(url_for('main_overview.overview'))