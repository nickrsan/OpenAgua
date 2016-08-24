from collections import OrderedDict
from flask import render_template, request, session, jsonify
from flask_user import login_required
from ..connection import connection

# import blueprint definition
from . import data_editor

@data_editor.route('/data_editor')
@login_required
def data_editor_main():    
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.call('get_network', {'network_id':session['network_id'],'include_data':'N'})
    template = conn.call('get_template',{'template_id':session['template_id']})
    features = OrderedDict()
    for t in template.types:
        resources = conn.call('get_resources_of_type', {'network_id':network.id, 'type_id':t.id})
        if resources:
            features[(t.id, t.name, t.resource_type)] = resources
    
    return render_template('data_editor.html',
                           features=features,
                           scenarios=network.scenarios)

@data_editor.route('/_get_variables', methods=['GET','POST'])
@login_required
def get_variables():
    conn = connection(url=session['url'], session_id=session['session_id'])
    type_id = int(request.args.get('type_id'))
    type_ = conn.call('get_templatetype', {'type_id':type_id})
    attrs = [a for a in type_.typeattrs if a.is_var=='N']
    
    return jsonify(result=attrs)

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

@data_editor.route('/_save_variable_data')
def _save_variable_data():
    conn = connection(url=session['url'], session_id=session['session_id'])
    
    attr_id = int(request.args.get('attr_id'))
    scen_id = int(request.args.get('scen_id'))
    dataset = request.args.get('attr_data')
    dataset = jsonify(dataset)
    
    args = {'scenario_id': scen_id, 'resource_attr_id': attr_id, 'dataset': dataset}
    result = conn.call('add_data_to_attribute', args)
    
    return jsonify(result=result)
