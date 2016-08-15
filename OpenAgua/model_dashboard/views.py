from __future__ import division, print_function
from sys import stderr
from flask import render_template, request, session, json, jsonify
from flask_user import login_required
from ..connection import connection

from subprocess import call

# import blueprint definition
from . import model_dashboard
from pyomo_model import model

@model_dashboard.route('/model_dashboard')
@login_required
def model_dashboard_main():
    
    # check status and progress of any running model
    status, progress = 0, 0 # default state
    
    return render_template('model_dashboard.html',
                           status=status,
                           progress=progress) 

@model_dashboard.route('/_run_model', methods=['POST'])
def run_model():

    # 1. get user input
    ti = '1/2000'
    tf = '12/2000'
    scenarios = ['Baseline', 'Re-operation 1', 'Re-operation 2']
    scids = [1,2,3] # need to get these from scenario
    
    # 2. define app name and arguments
    # in the future:
    # a. at least some of these should come in via the user interface (i.e. as a json string)
    # b. this should be passed on directly to the model server
    appname = 'OpenAguaModel'
    appfile = appname + '.py'
    args = dict(
        app = appname,
        url = session['url'],
        user = 'root',
        pw = 'password',
        sid = session['session_id'],
        nid = session['network_id'],
        tid = session['template_id'],
        scids = str(scids),
        ti = ti,
        tf = tf,
        tsf = '%m/%Y',
        log = 'logs')
    
    # 3. run the model as a subprocess
    # in the future, this will be via a web server call with json
    call = 'python {}'.format(appname)
    for k, v in args.iteritems():
        call += '-{} {}'.format(k, v)
        
    returncode = Popen(call)
    
    status = 1
    return jsonify(result={'status':status})

@model_dashboard.route('/_model_progress')
def model_progress():
    by_timestep = True
    #completed = model.get_progress(by_timestep = by_timestep)
    #if by_timestep:
        #progress = completed / (session['timestep_count'] * session['scenarios_count'])
    #else:
        #progress = completed / session['scenario_count']
    progress = 100
    return jsonify(result={'progress':progress})
