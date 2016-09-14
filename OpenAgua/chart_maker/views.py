from flask import render_template, request, session, json, jsonify
from flask_security import login_required
from ..connection import connection

# import blueprint definition
from . import chart_maker as cm

@cm.route('/chart_maker')
def chart_maker():
    return render_template('chart_maker.html')