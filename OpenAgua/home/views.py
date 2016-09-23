from flask import render_template, request, session, redirect, url_for
from flask_security import login_required, current_user

from ..connection import make_connection, create_hydrauser, load_hydrauser, \
     add_default_study
from . import user_home
from OpenAgua import app, db
from OpenAgua.models import User, HydraUrl, HydraUser, HydraStudy

@user_home.route('/home')
@login_required
def home():

    if current_user.new_user:
        
        # 1. create hydra user account
        create_hydrauser(db=db,
                         user_id=current_user.id,
                         hydra_url=app.config['HYDRA_URL'],
                         encrypt_key=app.config['SECRET_ENCRYPT_KEY'],
                         hydra_admin_username=app.config['HYDRA_ROOT_USERNAME'],
                         hydra_admin_password=app.config['HYDRA_ROOT_PASSWORD'],
                         hydra_user_username=current_user.email,
                         hydra_user_password='password')
        
        # 2. load just-created hydra user info
        load_hydrauser()
        
        # 3. connect to hydra using the now-loaded hydrauser info
        conn = make_connection()
        
        # 4. add defaults...
        
        add_default_study(conn, db,
                          app.config['DEFAULT_HYDRA_TEMPLATE'],
                          session['hydrauser_id'],
                          app.config['DEFAULT_SCENARIO_NAME'])
        
        # 5. turn off new_user flag
        user = User.query \
            .filter(User.email == current_user.email).first()  
        user.new_user = 0
        db.session.commit()
    
    else:
        # load hydrauser
        load_hydrauser()
        conn = make_connection()
    
    conn.load_active_study()
    
    if conn.invalid_study:
        return redirect(url_for('projects_manager.manage'))
    else:
        return redirect(url_for('main_overview.overview'))
    #return render_template('user_home.html')

# Load projects
@user_home.route('/_load_recent')
def load_recent():
    return redirect(url_for('main_overview.overview'))