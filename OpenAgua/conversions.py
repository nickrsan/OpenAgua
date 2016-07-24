import random

def get_project_by_name(conn, project_name):
    return conn.call('get_project_by_name', {'project_name':project_name})

def get_network_by_name(conn, project_name, network_name):
    project = get_project_by_name(conn, project_name)
    return conn.call('get_network_by_name', {'project_id':project.id, 'network_name':network_name})

def get_network(conn, network_id):
    return conn.call('get_network', {'network_id':network_id})    

# get shapes of type ftype
def get_shapes(shapes, ftype):
    return [s for s in shapes if s['geometry']['type']==ftype]

def add_network(conn, project_name):
    network = conn.call('add_network', {'net':{'nodes':[], 'links':[]}})    

def get_coords(network):
    coords = {}
    for n in network['nodes']:
        coords[n.id] = [float(n.x), float(n.y)] 
    return coords

# convert hydra nodes to geoJson for Leaflet
def nodes_geojson(nodes, coords):
    gj = []
    for node in nodes:
        if node.types:
            ftype = node.types[0] # assume only one template
            ftype_name = ftype.name
            template_name = ftype.template_name
        else:
            ftype_name = 'UNASSIGNED'
            template_name = 'UNASSIGNED'
        f = {'type':'Feature',
             'geometry':{'type':'Point',
                         'coordinates':coords[node.id]},
             'properties':{'name':node.name,
                           'description':node.description,
                           'nodetype':ftype_name,
                           'template':template_name,
                           'popupContent':'TEST'}} # hopefully this can be pretty fancy
        gj.append(f)
    return gj

def links_geojson(links, coords):
    gj = []
    for l in links:
        n1 = l['node_1_id']
        n2 = l['node_2_id']
        if l.types:
            ftype = l.types[0] # assume only one template
            ftype_name = ftype.name
            template_name = ftype.template_name
        else:
            ftype_name = 'UNASSIGNED'
            template_name = 'UNASSIGNED'
        f = {'type':'Feature',
             'geometry':{ 'type': 'LineString',
                          'coordinates': [coords[n1],coords[n2]] },
             'properties':{'name':l.name,
                           'description':l.description,
                           'linetype':ftype_name,
                           'template':template_name,
                           'popupContent':'TEST'}}

        gj.append(f)

    return gj

# make nodes - formatted as geoJson - from Leaflet
def make_nodes(shapes):
    nodes = []
    for s in shapes:
        x, y = s['geometry']['coordinates']
        n = dict(
            id = -1,
            #name = s['properties']['name'],
            name = 'Point' + str(random.randrange(0,1000)),
            description = 'It\'s a new node!',
            x = str(x),
            y = str(y)
        )
        nodes.append(n)
    return nodes

# make links - formatted as geoJson - from Leaflet
# need to account for multisegment lines
# for now, this assumes links lack vertices
def make_links(polylines, coords):
    d = 4 # rounding decimal points to match link coords with nodes.
    # p.s. This is annoying. It would be good to have geographic/topology capabilities built in to Hydra
    nlookup = {(round(x,d), round(y,d)): k for k, [x, y] in coords.items()}
    links = []
    for pl in polylines:
        xys = []
        for [x,y] in pl['geometry']['coordinates']:
            xy = (round(x,d), round(y,d))
            xys.append(xy)

        l = dict(
            id = -1,
            #name = pl['properties']['name'],
            name = 'Link' + str(random.randrange(0,1000)),
            description = 'It\'s a new link!',
            node_1_id = nlookup[xys[0]],
            node_2_id = nlookup[xys[1]]
        )
        links.append(l)
    return links

# use this to add shapes from Leaflet to Hydra
def add_features(conn, network_id, shapes):

    # modify to account for possibly no network... create network instead of add node

    # convert geoJson to Hydra features & write to Hydra
    points = get_shapes(shapes, 'Point')
    polylines = get_shapes(shapes, 'LineString')    

    if points:
        nodes = make_nodes(points)
        if nodes:
            nodes = conn.call('add_nodes', {'network_id': network_id, 'nodes': nodes})
    if polylines:
        network = get_network(conn, network_id)
        coords = get_coords(network)                   
        links = make_links(polylines, coords)
        if links:                         
            links = conn.call('add_links', {'network_id': network_id, 'links': links})

def get_features(network):
    coords = get_coords(network)
    nodes = nodes_geojson(network.nodes, coords)
    links = links_geojson(network.links, coords)
    features = nodes + links
    return features