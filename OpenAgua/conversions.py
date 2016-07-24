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
