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

@model_dashboard.route('/_run_model')
def run_model():

    # add model code here
    
    
    status = 1
    return jsonify(result={'status':status})

@model_dashboard.route('/_model_progress')
def model_progress():
    status = 1
    progress = 100 # get progress from running model
    return jsonify(result={'status':status, 'progress':progress})
