from collections import OrderedDict
from datetime import datetime

from flask import redirect, url_for, render_template, \
     request, session, jsonify, json
from flask_security import login_required, current_user
from ..connection import connection, make_connection, save_data, load_hydrauser
from ..utils import hydra_timeseries, d2o, \
     eval_scalar, eval_timeseries, eval_function, eval_data, get_dates, empty_timeseries

# import blueprint definition
from . import data_editor

@data_editor.route('/data_editor')
@login_required
def data_editor_main():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study()
    
    features = OrderedDict()
    
    for res_type in ['node','link']:
        for r in eval('conn.network.{}s'.format(res_type.lower())):
            ttype = [t for t in r.types if t.template_id == session['template_id']][0]
            if ttype.name in ['Inflow', 'Outflow', 'Junction', 'Withdrawal']:
                continue
            idx = (ttype.id, ttype.name, res_type)
            if idx not in features.keys():
                features[idx] = []
            features[idx].append(r)
            
    scenarios = [{'id':s.id, 'name':s.name} for s in conn.network.scenarios]
    
    return render_template('data_editor.html',
                           features=features,
                           scenarios=scenarios)

@data_editor.route('/_get_variables', methods=['GET','POST'])
@login_required
def get_variables():
    conn = make_connection()
    
    type_id = int(request.args.get('type_id'))
    feature_id = int(request.args.get('feature_id'))
    feature_type = request.args.get('feature_type').lower()
    res_attrs = conn.call('get_{}_attributes'.format(feature_type),
                          {'{}_id'.format(feature_type): feature_id,
                           'type_id':type_id})
    
    # add templatetype attribute information to each resource attribute
    
    # first, get the template type attributes
    ttype = conn.call('get_templatetype', {'type_id': type_id})
    attrs = {}
    for typeattr in ttype.typeattrs:
        attrs[typeattr.attr_id] = typeattr  
    
    # second, attach it to the resource attributes
    for i in range(len(res_attrs)):
        tpl_type_attr = attrs[res_attrs[i].attr_id]
        tpl_type_attr['name'] = tpl_type_attr.attr_name
        res_attrs[i]['tpl_type_attr'] = tpl_type_attr
    
    return jsonify(res_attrs=res_attrs)

@data_editor.route('/_get_variable_data')
@login_required
def get_variable_data():
    conn = make_connection()
    
    feature_type = request.args.get('feature_type').lower()
    feature_id = int(request.args.get('feature_id'))
    res_attr_id = int(request.args.get('res_attr_id'))
    scen_id = int(request.args.get('scen_id'))
    type_id = int(request.args.get('type_id'))
    data_type = request.args.get('data_type')

    args = {'%s_id' % feature_type: feature_id,
            'scenario_id': scen_id,
            'type_id': type_id}
    feature_data = conn.call('get_%s_data' % feature_type, args)
    
    res_attr_data = [row for row in feature_data if row.resource_attr_id == res_attr_id]
    
    eval_value = None
    if res_attr_data:
        
        # evaluate the data
        res_attr_data = res_attr_data[0]
        #data_type = res_attr_data.value.type
        
        function = None
        if data_type == 'timeseries':
            metadata = json.loads(res_attr_data.value.metadata)
            if 'function' in metadata.keys():
                if len(metadata['function']):
                    function = metadata['function']
        eval_value = eval_data(data_type, res_attr_data.value.value, function=function)
        
    if eval_value is None:
        res_attr_data = None
        if data_type == 'timeseries':
            eval_value = empty_timeseries()
        else:
            eval_value = ''
    
    return jsonify(res_attr_data=res_attr_data, eval_value=eval_value)

# add a new variable from user input
@data_editor.route('/_check_or_save_data', methods=['GET', 'POST'])
@login_required
def check_or_save_data():
    
    if request.method == 'POST':
        action = request.json['action']
        cur_data_type = request.json['cur_data_type']
        new_data = request.json['new_data']
        
        # create the data depending on data type    
        if cur_data_type in ['scalar', 'descriptor', 'function']:
            new_value = new_data
            
        elif cur_data_type == 'timeseries':
            new_value = hydra_timeseries(new_data)
            new_value = json.dumps(new_value)
            
        elif cur_data_type == 'array':
            new_value == None # placeholder
            
        # either way, we should check the data before saving
        errcode, errmsg, eval_value = eval_data(cur_data_type, new_value, do_eval=True)
        
        if action == 'save' and errcode == 1:
            conn = make_connection()
            
            orig_data_type = request.json['orig_data_type']
            res_attr = request.json['res_attr']
            res_attr_data = request.json['res_attr_data']
            scen_id = request.json['scen_id']
            
            metadata = {'source':'OpenAgua/%s' % current_user.email}
        
            status = save_data(conn, orig_data_type, cur_data_type,
                               res_attr, res_attr_data, new_value,
                               metadata, scen_id)
        else:
            status = 0 # no save attempt - just report error
        return jsonify(status=status, errcode=errcode, errmsg=errmsg, eval_value=eval_value)
    
    return redirect(url_for('data_editor.data_editor_main'))

