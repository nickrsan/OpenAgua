from flask import session, render_template, redirect, url_for
from flask_security import login_required

# import blueprint definition
from . import main_overview

from ..connection import make_connection, load_hydrauser

@main_overview.route('/overview')
@login_required
def overview():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study()
    if conn.invalid_study:
        return redirect(url_for('projects_manager.manage'))  
    
    return render_template('overview.html') 