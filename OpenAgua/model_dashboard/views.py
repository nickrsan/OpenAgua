from __future__ import division, print_function
from sys import stderr
from flask import render_template, request, session, json, jsonify
from ..connection import connection
from ..decorators import *

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

    # add model code here
    #1. define parameters
    params = dict(
        project = session['project_name'],
        start = (2000, 1),
        finish = (2000, 12)
    )
    print(params, file=stderr)
    
    #2. define scenarios
    scenarios = ['Baseline', 'Re-operation 1', 'Re-operation 2']
    session['timesteps_count'] = 12
    session['scenario_count'] = len(scenarios)
    print(scenarios, file=stderr)
    
    #3. run the model
    chunksize=5
    print(chunksize, file=stderr)
    #model.main(params, scenarios, chunksize)

@model_dashboard.route('/_model_progress')
def model_progress():
    by_timestep = True
    completed = model.get_progress(by_timestep = by_timestep)
    if by_timestep:
        progress = completed / (session['timestep_count'] * session['scenarios_count'])
    else:
        progress = completed / session['scenario_count']
    return jsonify(result={'progress':progress})
