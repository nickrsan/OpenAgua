from flask import session, render_template, redirect, url_for
from flask_security import login_required

# import blueprint definition
from . import study_overview

from ..connection import make_connection, load_hydrauser

@study_overview.route('/overview')
@login_required
def overview_main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    #conn.load_active_study()
    #if conn.invalid_study:
        #flash('danger', 'Oops!', 'Something went wrong. No study loaded.')
        #return redirect(url_for('home.home_main'))  
    
    return render_template('overview.html') 