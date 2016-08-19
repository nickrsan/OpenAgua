from flask import render_template, request, session, json, jsonify
from flask_user import login_required
from ..connection import connection

# import blueprint definition
from . import net_editor

def get_coords(network):
    coords = {}
    for n in network['nodes']:
        coords[n.id] = [float(n.x), float(n.y)] 
    return coords

@net_editor.route('/network_editor')
@login_required
def network_editor():
    conn = connection(url=session['url'], sessionid=session['sessionid'])
    template = conn.call('get_template', {'template_id':session['template_id']})
    ntypes = [t.name for t in template.types if t.resource_type == 'NODE']
    ltypes = [t.name for t in template.types if t.resource_type == 'LINK']
    
    return render_template('network_editor.html',
                           ntypes=ntypes,
                           ltypes=ltypes) 

@net_editor.route('/_load_network')
def load_network():
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    template = conn.call('get_template',{'template_id':session['template_id']})
    
    #features = features2gj(network, template)
    coords = get_coords(network)
    nodes = network.nodes
    links = network.links
    nodes_gj = [conn.make_geojson_from_node(node.id, session['template_name'], session['template_id']) for node in nodes]
    links_gj = [conn.make_geojson_from_link(link.id, session['template_name'], session['template_id'], coords) for link in links]
    features = nodes_gj + links_gj

    status_code = 1
    status_message = 'Network "%s" loaded' % session['network_name']

    features = json.dumps(features)
    
    result = dict(features=features, status_code=status_code, status_message=status_message)
    result_json = jsonify(result=result)
    return result_json

@net_editor.route('/_add_node')
def add_node():
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    template = conn.call('get_template',{'template_id':session['template_id']})

    new_node = request.args.get('new_node')
    gj = json.loads(new_node)

    new_gj = ''
    
    # check if the node already exists in the network
    if gj['properties']['name'] in [f.name for f in network.nodes]:
        status_code = -1
        
    # create the new node
    else:
        node_new = conn.make_node_from_geojson(gj, template=template)
        node = conn.call('add_node', {'network_id':session['network_id'], 'node':node_new})
        new_gj = [conn.make_geojson_from_node(node.id, session['template_name'], session['template_id'])]
        status_code = 1
    result = dict(new_gj=new_gj, status_code=status_code)
    return jsonify(result=result)

@net_editor.route('/_add_link')
def add_link():
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    template = conn.call('get_template',{'template_id':session['template_id']})

    new_link = request.args.get('new_link')
    gj = json.loads(new_link)

    new_gj = ''
    
    # check if the link already exists in the network
    if gj['properties']['name'] in [f.name for f in network.links]:
        status_code  = -1
        
    # create the new link(s)
    else:
        coords = get_coords(network)
        links_new = conn.make_links_from_geojson(gj, template, coords)
        links = conn.call('add_links', {'network_id':session['network_id'], 'links':links_new})
        if links:
            new_gj = []
            for link in links:
                gj = conn.make_geojson_from_link(link.id, session['template_name'], session['template_id'], coords)
                new_gj.append(gj)
            status_code = 1
        else:
            status_code = -1
    result = dict(new_gj=new_gj, status_code=status_code)
    return jsonify(result=result)

@net_editor.route('/_delete_feature')
def delete_feature():
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    
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
def purge_feature():
    conn = connection(url=session['url'], session_id=session['session_id'])
    network = conn.get_network(session['network_id'])
    
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
