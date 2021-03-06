import os
from subprocess import Popen, check_output
from datetime import datetime

from flask import render_template, request, session, json, jsonify, current_app
from flask_security import login_required

from OpenAgua import app
from ..connection import make_connection, load_hydrauser
from ..utils import decrypt

# import blueprint definition
from . import model_dashboard

@model_dashboard.route('/model_dashboard')
@login_required
def model_dashboard_main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study(load_from_hydra=False)
    scenarios = conn.get_scenarios(session['network_id']) # NB: we just need the IDs, so load from study instead
    # check status and progress of any running model
    status, progress = 0, 0 # default state
    
    #mgt_scen_grps = {
        #"Base scenario": ["Baseline"],
        #"Infrastructure": ["El Cuchillo Expansion","New Presa"],
        #"Hydrologic information": ["General forecasting","Santa Catarinia"],
        #"Environmental flows": ["El Cuchillo MIF", "Flood pulse program"],
        #"Efficiency improvements": ["Toilet replacement program"]
    #}
    
    return render_template('model_dashboard.html',
                           #mgt_scen_grps=mgt_scen_grps,
                           scenarios=scenarios,
                           status=status,
                           progress=progress) 

@model_dashboard.route('/_run_model', methods=['GET', 'POST'])
@login_required
def run_model():
    
    if request.method == 'POST':

        # 1. get user input
        scids = request.json['scids']
        #scids = [5] # need to get these from study / user
        session['scenarios_count'] = len(scids)
        
        session['pyomo_scen_dir'] = '{}@{}'.format(session['hydra_username'], datetime.now().strftime('%d%m%Y.%H%M%S'))
        
        # 2. define app name and arguments
        # in the future:
        # a. at least some of these should come in via the user interface (i.e. as a json string)
        # b. this should be passed on directly to the model server
        args = dict(
            app = app.config['PYOMO_APP_NAME'],
            url = session['hydra_url'],
            user = session['hydra_username'],
            pw = decrypt(session['hydra_password'], # POTENTIAL SECURITY CONCERN?
                         app.config['SECRET_ENCRYPT_KEY']),
            sid = session['hydra_sessionid'],
            nid = session['network_id'],
            tid = session['template_id'],
            uid = session['hydra_userid'],
            scids = '"%s"' % scids,
            ti = app.config['TEMP_TI'],
            tf = app.config['TEMP_TF'],
            tsf = app.config['TIMESTEP_FORMAT'],
            htsf = app.config['HYDRA_DATETIME_FORMAT'],
            fs = app.config['FORESIGHT'],
            sol = app.config['SOLVER'],
            ldir = session['pyomo_scen_dir']
        )
        
        # 3. run the model as a subprocess
        # in the future, this will be via a web server with json
        command = 'python %s' % app.config['PYOMO_APP_PATH']
        for k, v in args.items():
            command += ' -{} {}'.format(k, v)
        
        returncode = Popen(command)
        
        status = 0 # model started
        return jsonify(status=status)
    
    return redirect(url_for('model_dashboard.model_dashboard_main'))

@model_dashboard.route('/_model_progress')
def model_progress():
    command = ['python', app.config['PYOMO_CHECK_PATH'], '-ldir', session['pyomo_scen_dir']]
    try:
        result = check_output(command)
    except:
        status = -2 # failed
        ts_completed = 0
        ts_count = 0
        progress = 0
        main_log = None
        scen_log = None
        result = None
    else:
        result = json.loads(result.decode())
        ts_completed = result['completed']
        ts_count = result['count']
        main_log = result['main_log']
        scen_log = result['scen_log']
        progress = 0 # default when starting
        status = 2 # the model is running at least
        
    if ts_count:
        progress = ts_completed / (session['scenarios_count'] * ts_count) * 100
        if progress == 100:
            status = 3

    return jsonify(progress=int(progress), status=status, main_log=main_log, scen_log=scen_log)
