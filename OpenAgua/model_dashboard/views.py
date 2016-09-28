import os
from subprocess import Popen, check_output

from flask import render_template, request, session, json, jsonify, current_app
from flask_security import login_required

from OpenAgua import app
from ..connection import connection
from ..utils import decrypt

# import blueprint definition
from . import model_dashboard

@model_dashboard.route('/model_dashboard')
@login_required
def model_dashboard_main():
    
    # setup pyomo app directory
    
    session['app_path'] = app.config['PYOMO_APP_PATH']
    session['check_path'] = app.config['PYOMO_CHECK_PATH']
    session['app_name'] = app.config['PYOMO_APP_NAME']
    
    # check status and progress of any running model
    status, progress = 0, 0 # default state
    
    mgt_scen_grps = {
        "Base scenario": ["Baseline"],
        "Infrastructure": ["El Cuchillo Expansion","New Presa"],
        "Hydrologic information": ["General forecasting","Santa Catarinia"],
        "Environmental flows": ["El Cuchillo MIF", "Flood pulse program"],
        "Efficiency improvements": ["Toilet replacement program"]
    }
    
    return render_template('model_dashboard.html',
                           mgt_scen_grps=mgt_scen_grps,
                           status=status,
                           progress=progress) 

@model_dashboard.route('/_run_model', methods=['GET', 'POST'])
@login_required
def run_model():
    
    if request.method == 'GET':
        return redirect(url_for('model_dashboard.model_dashboard_main'))

    # 1. get user input
    ti = request.json['ti']
    tf = request.json['tf']
    #scids = request.json['scids']
    scids = [3] # need to get these from scenario
    session['scenarios_count'] = len(scids)
    
    # 2. define app name and arguments
    # in the future:
    # a. at least some of these should come in via the user interface (i.e. as a json string)
    # b. this should be passed on directly to the model server
    args = dict(
        app = session['app_name'],
        url = session['hydra_url'],
        user = session['hydra_username'],
        pw = decrypt(session['hydra_password'],
                     app.config['SECRET_ENCRYPT_KEY']),
        sid = session['hydra_sessionid'],
        nid = session['network_id'],
        tid = session['template_id'],
        uid = session['hydra_userid'],
        scids = '"%s"' % scids,
        ti = ti,
        tf = tf,
        tsf = '%m/%Y',
        htsf = '%Y-%m-%dT%H:%M:%S.%f000Z',
        sol = app.config['SOLVER']
    )
    
    # 3. run the model as a subprocess
    # in the future, this will be via a web server with json
    command = 'python %s' % session['app_path']
    for k, v in args.items():
        command += ' -{} {}'.format(k, v)
    
    returncode = Popen(command)
    
    status = 1
    return jsonify(status=status)

@model_dashboard.route('/_model_progress')
def model_progress():
    command = ['python', session['check_path'], '-dir', 'logs']
    result = subprocess.check_output(command)
    ts_completed = result['timesteps_completed']
    ts_count = result['timesteps_count']
    if ts_count is not None:
        progress = ts_completed / (session['scenarios_count'] * ts_count) * 100
    else:
        progress = 0
    return jsonify(result={'progress':int(progress)})
