import os
import shutil

from flask import redirect, url_for, render_template, request, session, jsonify, json
from flask_security import login_required, current_user
from ..connection import connection, make_connection, load_hydrauser, get_study_charts, delete_study_chart

from OpenAgua import app, db

# import blueprint definition
from . import chart_collection

@chart_collection.route('/chart_collection')
@login_required
def main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study()
    
    chartsobj = get_study_charts(session['study_id'])
    
    charts = []
    thumbnailspath = app.config['CHART_THUMBNAILS_PATH']
    chartspath = os.path.join(app.config['USER_FILES'], str(current_user.id), thumbnailspath)
    src = os.path.join(app.config['APP_ROOT'], chartspath)
    
    if not os.path.exists(src): # no charts have been created yet
        os.makedirs(src)
    
    # THIS SHOULD BE UPDATED!!!
    dst = os.path.join(app.config['APP_ROOT'], 'OpenAgua', 'static', chartspath)
    
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    
    for c in chartsobj:
        chart = {}
        chart['name'] = c.name
        chart['description'] = c.description
        
        staticdst = os.path.join('static', chartspath, c.thumbnail)
        chart['thumbnail'] = staticdst.replace('\\','/')
        chart['id'] = c.id
        charts.append(chart)
        
    return render_template('chart-collection.html', charts=charts)

@chart_collection.route('/_delete_chart', methods=['GET', 'POST'])
@login_required
def delete_chart():
    
    if request.method == 'POST':
        
        study_id = session['study_id']
        chart_id = request.json['chart_id']
        
        result = delete_study_chart(db, study_id, chart_id)
        
        # also remove delete chart from session
        if 'chart_id' in session and session['chart_id'] == chart_id:
            session['chart_id'] = None
        
        return jsonify(result=result)
        
    return redirect(url_for('chart_collection.main'))