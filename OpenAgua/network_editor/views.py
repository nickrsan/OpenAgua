from flask import redirect, url_for, render_template, request, session, json, \
     jsonify, g
from flask_security import login_required
from attrdict import AttrDict
from ..connection import make_connection, load_hydrauser

# import blueprint definition
from . import net_editor

@net_editor.route('/network_editor')
@login_required
def network_editor():
    load_hydrauser() # do this at the top of every page
    conn = make_connection(login=True)
    conn.load_active_study()
    if conn.invalid_study:
        return redirect(url_for('projects_manager.manage'))    
    
    ntypes = []
    ltypes = []
    for t in conn.template.types:
        if t.resource_type == 'NODE':
            typeattrs = [ta.attr_name for ta in t.typeattrs]
            if not( len(typeattrs)==2 and set(['inflow','outflow']).issubset(typeattrs) ):
                ntypes.append(t)
        elif t.resource_type == 'LINK':
            ltypes.append(t)

    return render_template('network_editor.html', ntypes=ntypes, ltypes=ltypes) 

@net_editor.route('/_load_network')
@login_required
def load_network():
    conn = make_connection()
    conn.load_active_study()
    
    features = conn.make_geojson_features()
    features = json.dumps(features)
    
    status_code = 1
    
    return jsonify(features=features, status_code=status_code)

@net_editor.route('/_add_node', methods=['GET', 'POST'])
@login_required
def add_node():
    
    if request.method=='POST':
        
        conn = make_connection()
        conn.load_active_study()
    
        gj = request.json
        
        # check if the node already exists in the network
        # NB: need to check if there can be duplicate names by 
        if gj['properties']['name'] in [f.name for f in conn.network.nodes]:
            status_code = -1
            old_node_id = None,
            new_gj = None
            
        # create the new node
        else:
            new_node, old_node_id = conn.add_node_from_geojson(gj)
            new_gj = [conn.make_geojson_from_node(new_node)]
            status_code = 1
        return jsonify(new_gj=new_gj, old_node_id=old_node_id, status_code=status_code)
    
    return redirect(url_for('net_editor.network_editor'))

@net_editor.route('/_add_link', methods=['GET', 'POST'])
@login_required
def add_link():
    
    if request.method == 'POST':
        conn = make_connection()
        conn.load_active_study()
    
        gj = request.json
    
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
    
    return redirect(url_for('net_editor.network_editor'))

@net_editor.route('/_edit_geometries', methods=['GET', 'POST'])
@login_required
def edit_geometries():
    
    if request.method == 'POST':
        conn = make_connection()
        conn.load_active_study(load_from_hydra=False)
        
        points = request.json['points']
        polylines = request.json['polylines']
        
        net = {'id': session['network_id']}
        statuscode = 0
        new_gj = []
        try:
            for point in points:
                f = AttrDict(point)
                node = f.properties
                lng, lat = f.geometry.coordinates
                node.x = str(lng)
                node.y = str(lat)
                response = conn.call('update_node', {'node': dict(node)})
    
            # reload the network with the moved nodes
            conn.load_active_study()
                
            for polyline in polylines:
                pl = AttrDict(polyline)
                coords = pl.geometry.coordinates
                if len(coords) == 2:
                    pass # no new nodes / endpoints are tied to existing nodes
                
                # create the new links...
                # IMPORTANT: We also need to pass any resource attribute info to any spawned links!
                links, nodes = conn.make_links_from_geojson(pl)
                
                # ...and purge old link
                conn.call('purge_link', {'link_id': pl.properties.id, 'purge_data': 'Y'})        
                
                # reload the network with the new links
                conn.load_active_study() 
                
                for link in links:
                    gj = conn.make_geojson_from_link(link)
                    new_gj.append(gj)
                        
                for node in nodes:
                    gj = conn.make_geojson_from_node(node)
                    new_gj.append(gj)
            statuscode = 1
        except:
            statuscode = -1
            
        return(jsonify(new_gj=new_gj, statuscode=statuscode))
    
    return redirect(url_for('net_editor.network_editor'))

@net_editor.route('/_delete_feature')
@login_required
def delete_feature():
    conn = make_connection()
    
    deleted_feature = request.args.get('deleted')
    gj = json.loads(deleted_feature)

    status_code = -1
    if gj['geometry']['type'] == 'Point':
        conn.call('delete_node', {'node_id': gj['properties']['id']})
        status_code = 1
    else:
        conn.call('delete_link', {'link_id': gj['properties']['id']})
        status_code = 1
    return jsonify(result=dict(status_code=status_code))

@net_editor.route('/_delete_layers', methods=['GET', 'POST'])
@login_required
def delete_layers():
    
    if request.method == 'POST':
        
        return jsonify(status_code = -1)

    return redirect(url_for('net_editor.network_editor'))

@net_editor.route('/_purge_replace_feature')
@login_required
def purge_replace_feature():
    conn = make_connection()
    conn.load_active_study()
    
    purged_feature = request.args.get('purged')
    gj = json.loads(purged_feature)

    status_code = -1
    new_gj = []
    if gj['geometry']['type'] == 'Point':
        new_node, del_links = conn.purge_replace_node(gj)
        if new_node:
            new_gj.append(conn.make_geojson_from_node(new_node))
            status_code = 1
        else:
            status_code = 0
    else:
        link_id = gj['properties']['id']
        conn.call('purge_link', {'link_id': link_id, 'purge_data':'Y'})
        del_links = [link_id]
        status_code = 1
    return jsonify(new_gj=new_gj, del_links=del_links, status_code=status_code)
