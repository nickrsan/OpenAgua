from collections import OrderedDict
from datetime import datetime

from flask import render_template, request, session, jsonify, json, g
from flask_user import login_required, current_user
from ..connection import connection
from ..utils import eval_scalar, eval_timeseries, eval_descriptor

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
        tpl_type_attr['pretty_name'] = tpl_type_attr.attr_name.replace('_',' ')
        res_attrs[i]['tpl_type_attr'] = tpl_type_attr
    
    return jsonify(res_attrs=res_attrs)

@data_editor.route('/_get_variable_data')
@login_required
def get_variable_data():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    feature_type = request.args.get('feature_type').lower()
    feature_id = int(request.args.get('feature_id'))
    attr_id = int(request.args.get('attr_id'))
    scen_id = int(request.args.get('scen_id'))
    type_id = int(request.args.get('type_id'))

    args = {'%s_id' % feature_type: feature_id,
            'scenario_id': scen_id,
            'type_id': type_id}
    feature_data = conn.call('get_%s_data' % feature_type, args)
    
    attr_data = [row for row in feature_data if row.attr_id==attr_id]
    if attr_data:
        
        attr_data = attr_data[0]
        
        # evaluate the data
        data_type = attr_data.value.type
        timeseries = eval('eval_{}(attr_data.value.value)'.format(data_type))
        
    else:
        attr_data = None
        
        # create some blank data for plotting
        timeseries = eval_scalar(None)
    
    return jsonify(attr_data=attr_data, timeseries=timeseries)

# add a new variable from user input
@data_editor.route('/_add_variable_data')
@login_required
def add_variable_data():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    scen_id = int(request.args.get('scen_id'))
    data_type = request.args.get('data_type')
    res_attr = json.loads(request.args.get('res_attr'))
    attr_data = json.loads(request.args.get('attr_data'))
    new_data = json.loads(request.args.get('new_data'))
    
    # create the data depending on data type
    if data_type == 'scalar':
        new_value = float(new_data)
    elif data_type == 'descriptor':
        new_value = new_data
    elif data_type == 'timeseries':
        new_value == None # placeholder
    
    if attr_data is not None:
        dataset = attr_data['value']
        dataset['value'] = new_value
    
        if dataset['type'] != data_type:
            conn.call('delete_resourcedata', {''})
            dataset['id'] = None
            dataset['type'] = data_type
            
    else: # create new dataset
        dataset = dict(
            id=None,
            type = data_type,
            name = res_attr['res_attr_name'],
            unit = res_attr['unit'],
            dimension = res_attr['dimension'],
            value = new_value,
            metadata = json.dumps({'source':'OpenAgua/%s' \
                                   % current_user.username})
        )        
    
    args = {'scenario_id': scen_id,
            'resource_attr_id': res_attr['res_attr_id'],
            'dataset': dataset}
    result = conn.call('add_data_to_attribute', args)
    if 'faultcode' in result.keys():
        status = -1
    else:
        status = 1
        
    # evaluate the data
    timeseries = eval('eval_{}(new_value)'.format(data_type))
    
    return jsonify(status = status, attr_data = result, timeseries = timeseries)

