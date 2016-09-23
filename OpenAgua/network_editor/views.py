from flask import redirect, url_for, render_template, request, session, json, \
     jsonify, g
from flask_security import login_required
from ..connection import make_connection, load_hydrauser

# import blueprint definition
from . import net_editor

@net_editor.route('/network_editor')
@login_required
def network_editor():
    load_hydrauser() # do this at the top of every page
    conn = make_connection()
    conn.load_active_study()
    if conn.invalid_study:
        return redirect(url_for('projects_manager.manage'))    
    
    ntypes = [t for t in conn.template.types if t.resource_type == 'NODE']
    ltypes = [t for t in conn.template.types if t.resource_type == 'LINK']

    return render_template('network_editor.html',
                           ntypes=ntypes,
                           ltypes=ltypes) 

@net_editor.route('/_load_network')
@login_required
def load_network():
    conn = make_connection()
    conn.load_active_study()
    
    features = conn.make_geojson_features()
    features = json.dumps(features)
    
    status_code = 1
    
    result = dict(features=features, status_code=status_code)
    
    return jsonify(result=result)

@net_editor.route('/_add_node')
@login_required
def add_node():
    conn = make_connection()
    conn.load_active_study()

    new_node = request.args.get('new_node')
    gj = json.loads(new_node)

    new_gj = ''
    
    # check if the node already exists in the network
    # NB: need to check if there can be duplicate names by 
    if gj['properties']['name'] in [f.name for f in conn.network.nodes]:
        status_code = -1
        
    # create the new node
    else:
        node_new = conn.make_node_from_geojson(gj)
        node = conn.call('add_node', {'network_id': session['network_id'],
                                      'node': node_new})
        new_gj = [conn.make_geojson_from_node(node)]
        status_code = 1
    result = dict(new_gj=new_gj, status_code=status_code)
    return jsonify(result=result)

@net_editor.route('/_add_link')
@login_required
def add_link():
    conn = make_connection()
    conn.load_active_study()

    new_link = request.args.get('new_link')
    gj = json.loads(new_link)

    new_gj = ''
    
    # check if the link already exists in the network
    if gj['properties']['name'] in [f.name for f in conn.network.links]:
        status_code  = -1
        
    # create the new link(s)
    else:
        hlinks, hnodes = conn.make_links_from_geojson(gj)
        conn.load_active_study() # reload the network with the new links
        status_code = -1
        new_gj = []
        if hlinks:
            for link in hlinks:
                gj = conn.make_geojson_from_link(link)
                new_gj.append(gj)
            status_code = 1
        if hnodes:
            for node in hnodes:
                gj = conn.make_geojson_from_node(node)
                new_gj.append(gj)
    return jsonify(new_gj=new_gj, status_code=status_code)

@net_editor.route('/_delete_feature')
@login_required
def delete_feature():
    conn = make_connection()
    
    deleted_feature = request.args.get('deleted')
    gj = json.loads(deleted_feature)

    status_code = -1
    if gj['geometry']['type'] == 'Point':
        conn.call('delete_node',{'node_id': gj['properties']['id']})
        status_code = 1
    else:
        conn.call('delete_link',{'link_id': gj['properties']['id']})
        status_code = 1
    return jsonify(result=dict(status_code=status_code))

@net_editor.route('/_purge_feature')
@login_required
def purge_feature():
    conn = make_connection()
    
    purged_feature = request.args.get('purged')
    gj = json.loads(purged_feature)

    status_code = -1
    if gj['geometry']['type'] == 'Point':
        conn.call('purge_node',{'node_id': gj['properties']['id'], 'purge_data':'Y'})
        status_code = 1
    else:
        conn.call('purge_link',{'link_id': gj['properties']['id'], 'purge_data':'Y'})
        status_code = 1
    return jsonify(result=dict(status_code=status_code))
