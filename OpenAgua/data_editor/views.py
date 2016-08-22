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
    
    return render_template('data_editor.html',
                           nodes = network.nodes,
                           links = network.links,
                           scenarios = network.scenarios)

@data_editor.route('/_get_variables', methods=['GET','POST'])
@login_required
def get_variables():
    conn = connection(url=session['url'], session_id=session['session_id'])
    feature_type = request.args.get('feature_type')
    feature_id = int(request.args.get('feature_id'))
    
    # this can be made more efficient with the use of get_resources_by_type in listing features
    # in data_editor, since then we can 1) organize by resource_type and 2) already have the resource type ID
    feature = conn.call('get_'+feature_type, {feature_type+'_id':feature_id})
    restypes = feature.types
    type_id = [t.id for t in restypes if t.template_id==session['template_id']][0]
    type_ = conn.call('get_templatetype', {'type_id':type_id})
    attrs = [a for a in type_.typeattrs if a.is_var=='N']
    
    return jsonify(result=attrs)