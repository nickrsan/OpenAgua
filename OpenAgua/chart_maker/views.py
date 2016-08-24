from flask import render_template, request, session, json, jsonify
from flask_user import login_required
from ..connection import connection

# import blueprint definition
from . import chart_maker

@chart_maker.route('/chart_maker')
def chart_maker_plotly():
    return render_template('chart_maker_plotly.html')