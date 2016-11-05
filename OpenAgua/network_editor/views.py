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

    return render_template('network-editor.html', ntypes=ntypes, ltypes=ltypes) 

@net_editor.route('/_load_network')
@login_required
def load_network():
    conn = make_connection()
    conn.load_active_study()
    
    points = conn.make_geojson_nodes()
    lines = conn.make_geojson_links()
    features = points + lines
    features = json.dumps(features)
    
    status_code = 1
    
    return jsonify(features=features, status_code=status_code)

@net_editor.route('/_add_node', methods=['GET', 'POST'])
@login_required
def add_node():
    
    if request.method=='POST':
        
        conn = make_connection()
        conn.load_active_study()
    
        gj = AttrDict(request.json['gj'])
        parent_link_id = request.json['parent_link_id']
        existing_node_id = request.json['existing_node_id']
        
        # check if the node already exists in the network
        # NB: need to check if there can be duplicate names by 
        if gj.properties.name in [f.name for f in conn.network.nodes]:
            status_code = -1
            new_gj = None
            
        # create the new node
        else:
            new_node = conn.add_node_from_geojson(gj)
            new_gj = [conn.make_geojson_from_node(new_node)]
            
            if parent_link_id:
            
                old_link = [l for l in conn.network.links if l.id == parent_link_id][0]
                
                # update old link, now ending at new node
                up_link = AttrDict(old_link.copy())
                up_link.node_2_id = new_node.id
                up_link.name = old_link.name + ' 01'
                up_link = conn.call('update_link', {'link': up_link})
                
                # create new downstream link
                down_link = AttrDict(old_link.copy())
                down_link.id = None
                down_link.name = old_link.name + ' 02'
                down_link.node_1_id = new_node.id
                down_link = conn.call('add_link', {'network_id': conn.network.id, 'link': down_link})
    
                conn.load_active_study() # reload the network
                for link in [up_link, down_link]:
                    new_gj.append(conn.make_geojson_from_link(link))
                    
            elif existing_node_id: # update existing links and delete old node
                conn.update_links(existing_node_id, new_node.id)
                conn.call('purge_node', {'node_id': existing_node_id})
            
            status_code = 1
        return jsonify(new_gj=new_gj, status_code=status_code)
    
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
            status_code = 1
            new_gj = []
            if hlinks:
                for link in hlinks:
                    gj = conn.make_geojson_from_link(link)
                    new_gj.append(gj)
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

@net_editor.route('/_delete_layers', methods=['GET', 'POST'])
@login_required
def delete_layers():
    
    if request.method == 'POST':
        
        conn = make_connection()
        conn.load_active_study(load_from_hydra=False)        
        
        status_code = 1
        features = AttrDict(request.json)
        node_ids = []
        for node in features.nodes:
            node_ids.append(node.id)
            result = conn.call('purge_node', {'node_id': node.id, 'purge_data': 'Y'})
            if 'faultcode' in result:
                status_code = -1
                break
        if status_code == 1:
            for link in features.links:
                if link.node_1_id in node_ids or link.node_2_id in node_ids:
                    continue # link was already purged
                result = conn.call('purge_link', {'link_id': link.id, 'purge_data': 'Y'})
                if 'faultcode' in result:
                    status_code = -1
                    break
        
        return jsonify(status_code=status_code)

    return redirect(url_for('net_editor.network_editor'))

@net_editor.route('/_purge_replace_feature', methods=['GET', 'POST'])
@login_required
def purge_replace_feature():
    
    if request.method == 'POST':
        
        conn = make_connection()
        conn.load_active_study()
        
        gj = AttrDict(request.json)
    
        status_code = -1
        new_gj = []
        if gj.geometry.type == 'Point':
            new_node, new_link, del_links = conn.purge_replace_node(gj)
            if new_node:
                new_gj.append(conn.make_geojson_from_node(new_node))
                status_code = 1
            if new_link:
                new_gj.append(conn.make_geojson_from_link(new_link))
                #status_code = 0
            else:
                status_code = 0
        else:
            link_id = gj.properties.id
            conn.call('purge_link', {'link_id': link_id, 'purge_data':'Y'})
            del_links = [link_id]
            status_code = 1
        return jsonify(new_gj=new_gj, del_links=del_links, status_code=status_code)
    
    return redirect(url_for('net_editor.network_editor'))

@net_editor.route('/_change_name_description', methods=['GET', 'POST'])
@login_required
def change_name_description():
    
    if request.method == 'POST':
        
        conn = make_connection()
        
        feature = AttrDict(request.json)
        if feature.type == 'Point':
            node = conn.get_node(feature.id)
            node['name'] = feature.name
            node['description'] = feature.description
            node['attributes'] = None
            result = conn.call('update_node', {'node': node})
        else:
            link = conn.get_link(feature.id)
            link['name'] = feature.name
            link['description'] = feature.description
            link['attributes'] = None
            result = conn.call('update_link', {'link': link})
        if 'faultcode' in result:
            status_code = -1
        else:
            status_code = 1
        
        return jsonify(status_code = status_code)
    
    return redirect(url_for('net_editor.network_editor'))
