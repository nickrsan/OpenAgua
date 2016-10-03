from flask import session, redirect, url_for, render_template
from flask_security import login_required, current_user

from OpenAgua import app

from .connection import connection

app.secret_key = app.config['SECRET_KEY']

@app.route('/')
def index():
    
    session['ti'] = '1/2000'
    session['tf'] = '12/2019'
    session['date_format'] = '%m/%Y'
    session['timestep'] = 'MONTHLY'
    session['hydra_time_format'] = '%Y-%m-01 00:00:00.000+0000'
    session['hydra_season_format'] = '9999-%m-01 00:00:00.000+0000'
    
    if current_user.is_authenticated:
        return redirect(url_for('home.home_main'))
    else:
        return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404