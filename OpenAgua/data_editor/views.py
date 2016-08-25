from collections import OrderedDict
from flask import render_template, request, session, jsonify, json
from flask_user import login_required
from flask_login import current_user
from ..connection import connection

# import blueprint definition
from . import data_editor

global attr_dict

@data_editor.route('/data_editor')
@login_required
def data_editor_main():    
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.call('get_network', {'network_id':session['network_id'],'include_data':'N'})
    template = conn.call('get_template',{'template_id':session['template_id']})
    features = OrderedDict()   
    
    for res_type in ['NETWORK','NODE','LINK']:
        for ttype in template.types:
            #resources = conn.call('get_resources_of_type', {'network_id':network.id, 'type_id':t.id})
            if ttype.resource_type=='NETWORK':
                nodes = [n for n in network.nodes if ttype.id in [t.id for t in n.types]]
                if nodes:
                    features[(ttype.id, ttype.name, ttype.resource_type)] = nodes
            elif ttype.resource_type=='NODE':
                nodes = [n for n in network.nodes if ttype.id in [t.id for t in n.types]]
                if nodes:
                    features[(ttype.id, ttype.name, ttype.resource_type)] = nodes
            elif ttype.resource_type=='LINK':
                nodes = [n for n in network.nodes if ttype.id in [t.id for t in n.types]]
                if nodes:
                    features[(ttype.id, ttype.name, ttype.resource_type)] = nodes
        
            
    # create an attribute lookup dictionary
    global attr_dict
    attrs = conn.call('get_template_attributes', {'template_id':session['template_id']})
    attr_dict = {}
    for a in attrs:
        attr_dict[a.id] = a.name    
    
    return render_template('data_editor.html',
                           features=features,
                           scenarios=network.scenarios)

@data_editor.route('/_get_variables', methods=['GET','POST'])
@login_required
def get_variables():
    global attr_dict
    
    conn = connection(url=session['url'], session_id=session['session_id'])
    type_id = int(request.args.get('type_id'))
    feature_id = int(request.args.get('feature_id'))
    feature_type = request.args.get('feature_type').lower()
    res_attrs = conn.call('get_%s_attributes'%feature_type, {'%s_id'%feature_type: feature_id, 'type_id':type_id})
    
    return jsonify(res_attrs=res_attrs, attr_dict=attr_dict)

@data_editor.route('/_get_variable_data')
@login_required
def get_variable_data():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    feature_type = request.args.get('feature_type').lower()
    feature_id = int(request.args.get('feature_id'))
    attr_id = int(request.args.get('attr_id'))
    scen_id = int(request.args.get('scen_id'))
    type_id = int(request.args.get('type_id'))

    args = {'%s_id' % feature_type: feature_id, 'scenario_id': scen_id, 'type_id': type_id}
    feature_data = conn.call('get_%s_data' % feature_type, args)
    
    attr_data = [row for row in feature_data if row.attr_id==attr_id]
    if attr_data:
        attr_data = attr_data[0]
    else:
        attr_data = None
    
    return jsonify(result=attr_data)

# add a new variable from user input
@data_editor.route('/_add_variable_data')
@login_required
def add_variable_data():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    res_attr_id = int(request.args.get('res_attr_id'))
    attr_id = int(request.args.get('attr_id'))
    scen_id = int(request.args.get('scen_id'))
    val = request.args.get('val')
    
    # we need to create Dataset. Since we are attaching it to an existing attribute, we will
    # use the same dimensions, units, etc. as that attribute.
    attr = conn.call('get_attribute_by_id', {'ID':attr_id})
    
    dataset = dict(
        id=None,
        type = 'descriptor',
        name = attr.name,
        unit = None,
        dimension = attr.dimen,
        value = val,
        metadata = json.dumps({'source':'OpenAgua/%s' % current_user.username})
    )    
    
    args = {'scenario_id': scen_id, 'resource_attr_id': res_attr_id, 'dataset': dataset}
    result = conn.call('add_data_to_attribute', args)
    if 'faultcode' in result.keys():
        status = -1
    else:
        status = 1
    
    return jsonify(status=status)

@data_editor.route('/_update_variable_data')
@login_required
def _update_variable_data():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    scen_id = int(request.args.get('scen_id'))
    dataset = request.args.get('attr_data')
    dataset = json.loads(dataset)
    dataset['metadata'] = json.dumps({'source':'OpenAgua/%s' % current_user.username})
    
    args = {'scenario_id': scen_id, 'resource_attr_id': dataset['resource_attr_id'], 'dataset': dataset['value']}
    result = conn.call('add_data_to_attribute', args)
    if 'faultcode' in result.keys():
        status = -1
    else:
        status = 1
    
    return jsonify(status=status)
