import os
import pandas
import base64

from flask import Blueprint, redirect, url_for, render_template, request, session, jsonify, json
from flask_security import login_required, current_user

from attrdict import AttrDict

from ..connection import connection, make_connection, save_data, load_hydrauser, add_chart, load_study_chart

from OpenAgua import app, db

# blueprint definition
from . import chart_maker

@chart_maker.route('/chart_maker')
@login_required
def main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study()
    #res_attrs = conn.get_res_attrs()
    #res_types = {'Nodes': {}, 'Links': {}}
    #for n in conn.network.nodes:
        #res_type = [rt for rt in n.types if rt.template_id == conn.template.id][0]
        #if res_type.type_id not in res_types['Nodes']:
            #res_types['Nodes'][res_type.type_id] = res_type.name
    
    if 'chart_id' not in session or session['chart_id'] == None:
        setup = {'renderer': app.config['DEFAULT_CHART_RENDERER'],
                 'config': {}}
    else:
        chart = load_study_chart(session['study_id'], session['chart_id'])
        filters = json.loads(chart.filters)
        setup = json.loads(chart.setup)
    #session['chart_id'] = None

    return render_template('chart-maker.html', ttypes=conn.ttypes, filters=filters, setup=setup)

@chart_maker.route('/_load_chart')
@login_required
def load_chart():
    session['chart_id'] = request.args.get('chart_id', type=int)
    return jsonify(redirect=url_for('chart_maker.main'))

@chart_maker.route('/_load_pivot_data')
@login_required
def load_pivot_data():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study(include_data=True)
    res_attrs = conn.get_res_attrs()
    
    filter_by_type = False
    filter_by_attr = False
    filters = AttrDict(json.loads(request.args.get('filters')))
    if filters and filters.filterby == 'res_type':
        filter_by_type = True
        if filters.attr_ids:
            filter_by_attr = True
    
    data = []
    if filter_by_attr:
        datadict = {} # we will postprocess the data
    for sc in conn.network.scenarios:
        scen_name = sc.name
        for rs in sc.resourcescenarios:
            
            ra = res_attrs[rs.resource_attr_id]
            
            if rs.value.type != 'timeseries':
                continue
            
            metadata = json.loads(rs.value.metadata)
            #if 'function' in metadata and len(metadata['function']):
                #continue # for now - need to fix
            
            # add filters here
            if filter_by_attr and rs.attr_id not in filters.attr_ids:
                continue            
            if filter_by_type and conn.ttype_dict[ra.res_type] not in filters.ttype_ids:
                continue
            
            # the following needs updating if more than one timeseries item, but it is otherwise effective
            timeseries = pandas.read_json(json.dumps(json.loads(rs.value.value)['0']), typ='series')
            for d, v in timeseries.iteritems():
                if type(v) == pandas.tslib.NaTType:
                    value = 0
                else:
                    value = float(v)
                
                if filter_by_attr: # attrs are columns
                    key = (scen_name, ra.res_name, ra.res_type, d.year, d.month)
                    if key not in datadict:
                        datadict[key] = {}
                    datadict[key][ra.attr_name] = value
                else: # attrs are in rows
                    data.append({
                        'scenario': scen_name,
                        'feature': ra.res_name,
                        'feature type': ra.res_type,
                        'variable': ra.attr_name,
                        'year': d.year,
                        'month': d.month,
                        'value': value
                    })
    if filter_by_attr:
        data = []
        headers = ['scenario','feature','feature type','year','month']
        #variables = data.items()[0].keys()
        for key in datadict:
            row = {}
            for i, n in enumerate(headers):
                row[n] = key[i]
            for i, v in enumerate(datadict[key].keys()):
                row[v] = datadict[key][v]
            data.append(row)
        
    return jsonify(data=data)

@chart_maker.route('/_save_chart', methods=['GET', 'POST'])
@login_required
def save_chart():
    
    if request.method == 'POST':
        
        hydrastudy_id = session['study_id']
        
        thumbnail = request.form['thumbnail']
        name = request.form['name']
        description = request.form['description']
        filters = request.form['filters']
        setup = request.form['setup']
        
        # save image to file
        userfiles = os.path.join(app.config['USER_FILES'], str(current_user.id)) # testing for now
        thumbnailspath = app.config['CHART_THUMBNAILS_PATH']
        thumbnailsabspath = os.path.join(userfiles, thumbnailspath)
        if not os.path.exists(thumbnailsabspath):
            os.makedirs(thumbnailsabspath)
        filename = '{}.png'.format(name.replace(' ', '-'))
        thumbnailabspath = os.path.join(userfiles, thumbnailspath, filename)
        
        imgstr = thumbnail.split(',')[1].encode()
        with open(thumbnailabspath, "wb") as f:
            f.write(base64.decodestring(imgstr))
                
        add_chart(db, hydrastudy_id, name, description, filename, filters, setup)
    
        return jsonify(result = 0)
    
    return redirect(url_for('chart_maker.main'))