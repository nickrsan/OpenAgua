from flask import render_template, request, session, redirect, url_for
from flask_security import login_required, current_user

from ..connection import make_connection, create_hydrauser, load_hydrauser
from . import user_home
from OpenAgua import app, db
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
                         hydra_user_username=current_user.email,
                         hydra_user_password='password')
        
        # update the user new_user flag
        user = User.query \
            .filter(User.email == current_user.email).first()  
        user.new_user = False  
    
    # load hydrauser
    load_hydrauser()
    conn = make_connection(session, include_network=False, 
                          include_template=False)
    conn.load_active_study()

    return redirect(url_for('main_overview.overview'))
    #return render_template('user_home.html')

# Load projects
@user_home.route('/_load_recent')
def load_recent():
    return redirect(url_for('main_overview.overview'))