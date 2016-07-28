import random    

# get shapes of type ftype
def get_shapes(shapes, ftype):
    return [s for s in shapes if s['geometry']['type']==ftype]

def get_coords(network):
    coords = {}
    for n in network['nodes']:
        coords[n.id] = [float(n.x), float(n.y)] 
    return coords

# convert hydra nodes to geoJson for Leaflet
def hyd2gj_nodes(nodes, template_id):
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
                         'coordinates':[node.x, node.y]},
             'properties':{'name':node.name,
                           'id':node.id,
                           'description':node.description,
                           'nodetype':ftype_name,
                           'template':template_name}} # hopefully this can be pretty fancy
        gj.append(f)

    return gj

def hyd2gj_links(links, coords):
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
                           'id':l.id,
                           'description':l.description,
                           'linetype':ftype_name,
                           'template':template_name}}

        gj.append(f)

    return gj

# convert geoJson nodes to Hydra nodes
def gj2hyd_point(shape):
    x, y = shape['geometry']['coordinates']
    node = dict(
        id = -1,
        name = shape['properties']['name'],
        description = shape['properties']['description'],
        x = str(x),
        y = str(y)
    )
    return node

# convert geoJson polylines to Hydra links
# note that this accounts for multisegment lines by splitting up the segment into pieces
# for now, this assumes links lack vertices that are not on existing nodes
def gj2hyd_polyline(polyline, coords):
    d = 4 # rounding decimal points to match link coords with nodes.
    # p.s. This is annoying. It would be good to have geographic/topology capabilities built in to Hydra
    nlookup = {(round(x,d), round(y,d)): k for k, [x, y] in coords.items()}
    xys = []
    for [x,y] in polyline['geometry']['coordinates']:
        xy = (round(x,d), round(y,d))
        xys.append(xy)

    links = []
    nsegments = len(xys) - 1
    for i in range(nsegments):
        link = dict(
            id = -1,
            name = '{}_{:02}'.format(polyline['properties']['name'], i+1),
            description = '{} (Segment {})'.format(polyline['properties']['description'], i+1),
            node_1_id = nlookup[xys[i]],
            node_2_id = nlookup[xys[i+1]]
        )
    links.append(link)
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
        network = conn.get_network(network_id)
        coords = get_coords(network)                   
        links = make_links(polylines, coords)
        if links:                         
            links = conn.call('add_links', {'network_id': network_id, 'links': links})

# converts Hydra network to geojson nodes and links
def features2gj(network):
    coords = get_coords(network)
    nodes = hyd2gj_nodes(network.nodes)
    links = hyd2gj_links(network.links, coords)
    features = nodes + links
    return features