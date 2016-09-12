from collections import OrderedDict
from datetime import datetime

from flask import render_template, request, session, jsonify, json, g
from flask_user import login_required, current_user
from ..connection import connection, make_connection, save_data
from ..utils import hydra_timeseries, d2o, \
     eval_scalar, eval_timeseries, eval_function, eval_data

# import blueprint definition
from . import data_editor

@data_editor.route('/data_editor')
@login_required
def data_editor_main():    
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.call('get_network', {'network_id':session['network_id'],
                                        'include_data':'N'})
    template = conn.call('get_template',{'template_id':session['template_id']})
    features = OrderedDict()
    
    for res_type in ['NETWORK','NODE','LINK']:
        for ttype in template.types:            
            if ttype.resource_type=='NETWORK':
                pass # not sure how to load these
            elif ttype.resource_type==res_type:
                feats = [r for r in eval('network.{}s' \
                                         .format(res_type.lower())) \
                         if ttype.id in [t.id for t in r.types]]
                if feats:
                    features[(ttype.id, ttype.name.replace('_', ' '),
                              ttype.resource_type)] = feats
    
    return render_template('data_editor.html',
                           features=features,
                           scenarios=network.scenarios)

@data_editor.route('/_get_variables', methods=['GET','POST'])
@login_required
def get_variables():
    
    conn = connection(url=session['url'], session_id=session['session_id'])
    type_id = int(request.args.get('type_id'))
    feature_id = int(request.args.get('feature_id'))
    feature_type = request.args.get('feature_type').lower()
    res_attrs = conn.call('get_%s_attributes'%feature_type,
                          {'%s_id'%feature_type: feature_id, 'type_id':type_id})
    
    # add templatetype attribute information to each resource attribute,
    # so we can display useful variable information in the data editor
    
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
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    feature_type = request.args.get('feature_type').lower()
    feature_id = int(request.args.get('feature_id'))
    res_attr_id = int(request.args.get('res_attr_id'))
    scen_id = int(request.args.get('scen_id'))
    type_id = int(request.args.get('type_id'))

    args = {'%s_id' % feature_type: feature_id,
            'scenario_id': scen_id,
            'type_id': type_id}
    feature_data = conn.call('get_%s_data' % feature_type, args)
    
    res_attr_data = \
        [row for row in feature_data if row.resource_attr_id == res_attr_id]

    if res_attr_data:
        
        # evaluate the data
        res_attr_data = res_attr_data[0]
        data_type = res_attr_data.value.type
        
        function = None
        if data_type == 'timeseries':
            metadata = json.loads(res_attr_data.value.metadata)
            if 'function' in metadata.keys():
                if len(metadata['function']):
                    function = metadata['function']
        timeseries = eval_data(data_type,
                               res_attr_data.value.value, function = function)
        
    else:
        res_attr_data = None
        
        # create some blank data for plotting
        timeseries = eval_data('generic', None)
    
    return jsonify(res_attr_data=res_attr_data, timeseries=timeseries)

# add a new variable from user input
@data_editor.route('/_check_or_save_data')
@login_required
def check_or_save_data():
    
    action = request.args.get('action')
    cur_data_type = request.args.get('cur_data_type')
    new_data = json.loads(request.args.get('new_data'))
    
    # create the data depending on data type    
    if cur_data_type in ['scalar', 'descriptor', 'function']:
        new_value = new_data
        
    elif cur_data_type == 'timeseries':
        new_value = hydra_timeseries(new_data)
        new_value = json.dumps(new_value)
        
    elif cur_data_type == 'array':
        new_value == None # placeholder
        
    # either way, we should check the data before saving
    errcode, errmsg, timeseries = \
        eval_data(cur_data_type, new_value, do_eval=True)
    
    if action == 'save' and errcode == 1:
        conn = make_connection(session,
                               include_network=False, include_template=False)
        
        orig_data_type = request.args.get('orig_data_type')
        res_attr = json.loads(request.args.get('res_attr'))
        res_attr_data = json.loads(request.args.get('res_attr_data'))    
        scen_id = int(request.args.get('scen_id'))
        
        metadata = {'source':'OpenAgua/%s' % current_user.username}
    
        status = save_data(conn, orig_data_type, cur_data_type,
                           res_attr, res_attr_data, new_value,
                           metadata, scen_id)
    else:
        status = 0 # no save attempt - just report error
        
    result = jsonify(status = status,
                     errcode = errcode,
                     errmsg = errmsg,
                     timeseries = timeseries)
    return result

