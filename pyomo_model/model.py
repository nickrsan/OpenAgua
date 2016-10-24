import json

from pyomo.environ import ConcreteModel, Set, Objective, Var, Param, Constraint, NonNegativeReals, maximize, summation
from attrdict import AttrDict

from utils import eval_function

def create_model(model_name, nodes, links, type_nodes, type_links, timesteps, p):

    model = ConcreteModel(name = model_name)
    
    # sets
    
    # basic sets
    model.Nodes = Set(initialize=nodes)
    model.Links = Set(initialize=links)
    model.TS = Set(initialize=timesteps, ordered=True)
    
    def NodesIn_init(model, node):
        retval = []
        for (i,j) in model.Links:
            if j == node:
                retval.append(i)
        return retval
    model.NodesIn = Set(model.Nodes, initialize=NodesIn_init)
    
    def NodesOut_init(model, node):
        retval = []
        for (j,k) in model.Links:
            if j == node:
                retval.append(k)
        return retval
    model.NodesOut = Set(model.Nodes, initialize=NodesOut_init)    
    
    # create sets (nodes or links) for each template type
    for k, v in type_nodes.items():
        exec('model.{} = Set(within=model.Nodes, initialize={})'.format(k, v))
    for k, v in type_links.items():
        exec('model.{} = Set(within=model.Links, initialize={})'.format(k, v))
    
    # create set for non-storage nodes
    if 'Reservoir' in model:
        model.Non_reservoir = model.Nodes - model.Reservoir
    
    # variables
    if 'Reservoir' in model:
        model.S = Var(model.Reservoir * model.TS, domain=NonNegativeReals) # storage
        model.D = Var(model.Non_reservoir * model.TS, domain=NonNegativeReals) # delivery
    else:
        model.D = Var(model.Nodes * model.TS, domain=NonNegativeReals) # delivery
    model.G = Var(model.Nodes * model.TS, domain=NonNegativeReals) # gain (local inflow)
    model.L = Var(model.Nodes * model.TS, domain=NonNegativeReals) # loss (local outflow)
    model.Q = Var(model.Links * model.TS, domain=NonNegativeReals) # flow in links
    
    model.I = Var(model.Nodes * model.TS, domain=NonNegativeReals) # total inflow to a node
    model.O = Var(model.Nodes * model.TS, domain=NonNegativeReals) # total outflow from a node
    
    # parameters 
    
    def InitialStorage(model, j):
        return p.node['Initial_Storage'][j]
    if 'Reservoir' in model:
        model.Si = Param(model.Reservoir, rule=InitialStorage)
    
    def NodePriority_rule(model, j, t):
        priority = -1 # default 
        if 'Priority' in p.node.keys() and (j, t) in p.node['Priority'].keys():
            priority = p.node['Priority'][(j, t)]
        elif j in model.Outflow:
            priority = 0
        return priority
    if 'Reservoir' in model:
        model.Demand_Priority = Param(model.Non_reservoir, model.TS, rule=NodePriority_rule)
        model.Storage_Priority = Param(model.Reservoir, model.TS, rule=NodePriority_rule)
    else:
        model.Demand_Priority = Param(model.Nodes, model.TS, rule=NodePriority_rule)
    
    def LinkPriority_rule(model, i, j, t):
        priority = 0
        if 'Priority' in p.link.keys() and (i, j, t) in p.link['Priority'].keys():
            priority = p.link['Priority'][(i, j, t)]
        return priority
    model.Flow_Priority = Param(model.Links, model.TS, rule=LinkPriority_rule)
    
    # constraints
    
    #def Inflow_rule(model, j, t): # not to be confused with Inflow resources
        #return model.I[j,t] == sum(model.Q[i,j,t] for i in model.NodesIn[j])
    #model.Inflow_definition = Constraint(model.Nodes, model.TS, rule=Inflow_rule)
    
    #def Outflow_rule(model, j, t): # not to be confused with Outflow resources
        #return model.O[j,t] == sum(model.Q[j,k,t] for k in model.NodesOut[j])
    #model.Outflow_definition = Constraint(model.Nodes, model.TS, rule=Outflow_rule)
    
    def StorageMassBalance_rule(model, j, t):
        if t == model.TS.first():
            return model.Si[j] - model.S[j, t] \
                   + model.G[j, t] + model.I[j,t] \
                   - model.L[j, t] - model.O[j,t] == 0
        else:
            return model.S[j, model.TS.prev(t)] - model.S[j, t] \
                   + model.G[j, t] + model.I[j,t] \
                   - model.L[j, t] - model.O[j,t] == 0
    def NonStorageMassBalance_rule(model, j, t):
        return model.G[j, t] + model.I[j,t] \
               - model.L[j, t] - model.O[j,t] == 0
    if 'Reservoir' in model:
        model.StorageMassBalance = Constraint(model.Reservoir, model.TS, rule=StorageMassBalance_rule)
        model.NonStorageMassBalance = Constraint(model.Non_reservoir, model.TS, rule=NonStorageMassBalance_rule)
    else:
        model.NonStorageMassBalance = Constraint(model.Nodes, model.TS, rule=NonStorageMassBalance_rule)
        
    #def Delivery_rule(model, j, t): # this is redundant with inflow, but more explicit
        #return model.D[j,t] == sum(model.Q[i,j,t] for i in model.NodesIn[j])
    #if 'Reservoir' in model:
        #model.Delivery = Constraint(model.Non_reservoir, model.TS, rule=Delivery_rule)
    #else:
        #model.Delivery = Constraint(model.Nodes, model.TS, rule=Delivery_rule)
    
    def ChannelCap_rule(model, i, j, t):
        if 'River' in model and (i,j) in model.River:
            return Constraint.Skip
        elif 'Return_Flow' in model and (i,j) in model.Return_Flow:
            return Constraint.Skip
        elif 'Flow_Capacity' in p.link.keys() and (i,j,t) in p.link['Flow_Capacity'].keys():
            return (0, model.Q[i,j,t], p.link['Flow_Capacity'][(i,j,t)])
        else:
            return (0, model.Q[i,j,t], 0)
    model.ChannelCapacity = Constraint(model.Links, model.TS, rule=ChannelCap_rule)
    
    ## NB: delivery should be constrained by delivery link capacity, not actual demand, which
    ## will be driven by economics
    #def DeliveryCap_rule(model, j, t):
        #if 'Demand' in p.node.keys() and (j,t) in p.node['Demand'].keys():
            #return (0, model.D[j,t], p.node['Demand'][(j,t)])
        #else:
            #return Constraint.Skip
    #model.DeliveryCap = Constraint(model.Non_reservoir, model.TS, rule=DeliveryCap_rule)
    
    def StorageBounds_rule(model, j, t):
        return (p.node['Inactive_Pool'][(j,t)], model.S[j,t], p.node['Storage_Capacity'][(j,t)])
    if 'Reservoir' in model:
        model.StorageBounds = Constraint(model.Reservoir, model.TS, rule=StorageBounds_rule)
    
    # boundary conditions
    
    # this will be expanded significantly
    def LocalGain_rule(model, j, t):
        if 'Runoff' in p.node.keys() and (j,t) in p.node['Runoff'].keys():
            return model.G[j,t] == p.node['Runoff'][(j,t)]
        else:
            return model.G[j,t] == 0
    model.Local_Gain = Constraint(model.Nodes, model.TS, rule=LocalGain_rule)
    
    # this will also be expanded to account for loss to groundwater, etc.
    def LocalLoss_rule(model, j, t):
        if j in model.Outflow:
            return Constraint.Skip
        elif 'Consumption' in p.node.keys() and (j,t) in p.node['Consumption']:
            return model.L[j,t] == model.D[j,t] * p.node['Consumption'][(j,t)] / 100
        else:
            return model.L[j,t] == 0 # this should be specified as a default
    model.Local_Loss = Constraint(model.Nodes, model.TS, rule=LocalLoss_rule)
    
    # objective function
    
    def Objective_fn_storage(model):
        return summation(model.Demand_Priority, model.D) \
            + summation(model.Storage_Priority, model.S) \
            + summation(model.Flow_Priority, model.Q)
    def Objective_fn_nostorage(model):
        return summation(model.Demand_Priority, model.D) \
            + summation(model.Flow_Priority, model.Q)
    if 'Reservoir' in model:
        model.Ojective = Objective(rule=Objective_fn_storage, sense=maximize)
    else:
        model.Ojective = Objective(rule=Objective_fn_nostorage, sense=maximize)
    
    return model

def prepare_model(model_name, network, template, attr_names, timestep_dict):
#def prepare_model(model_name, network, attrs, timestep_dict):
    
    # prepare data - we could move some of this to elsewhere 
    
    template_id = template.id
    
    # extract info about nodes & links
    
    res_attrs = {}
    
    # NODES
    nodes = []
    type_nodes = {}
    for n in network.nodes:
        
        # a list of all nodes
        nodes.append(n.id)
        
        # a dictionary of template_type to node_id
        for t in n.types:
            if t.template_id == template_id:
                type_name = t.name.replace(' ', '_')
                
                if type_name not in type_nodes.keys():
                    type_nodes[type_name] = []
                type_nodes[type_name].append(n.id)
            
        # general resource attribute information    
        for ra in n.attributes:
            res_attrs[ra.id] = AttrDict({'name': attr_names[ra.attr_id], 'is_var': ra.attr_is_var})           
                
    # LINKS
    links = []
    link_nodes = {}
    type_links = {}
    for l in network.links:
        node_ids = [l.node_1_id, l.node_2_id]
        
        # a list of all links
        links.append(tuple(node_ids))
        
        # a dictionary of link_id to [node_1_id, node_2_id]
        link_nodes[l.id] = node_ids
        
        # a dictionary of template type to [node_1_id, node_2_id]
        for t in l.types:
            if t.template_id == template_id:
                type_name = t.name.replace(' ', '_')
                if type_name not in type_links.keys():
                    type_links[type_name] = []
                type_links[type_name].append(tuple(node_ids))
        
        # general resource attribute information    
        for ra in l.attributes:
            res_attrs[ra.id] = AttrDict({'name': attr_names[ra.attr_id], 'is_var': ra.attr_is_var})          
    
    # extract info about time steps
    timesteps = [ot for (ht, ot) in timestep_dict.values()]
    
    # initialize dictionary of parameters
    p = AttrDict({ft: AttrDict({}) for ft in ['node', 'link', 'net']})
    
    ra_node = {} # res_attr to node lookup
    for node in network.nodes:
        for ra in node.attributes:
            ra_node[ra.id] = node.id
    
    ra_link = {} # res_attr to link lookup
    for link in network.links:
        for ra in link.attributes:
            ra_link[ra.id] = link.id
            
    #ra_net = dict() # res_attr to network lookup
    #for link in network.links:
        #for res_attr in link.attributes:
            #ra_link[res_attr.id] = link.id
            
    resourcescenarios = network.scenarios[0].resourcescenarios    
    
    for rs in resourcescenarios:
        
        ra_id = rs.resource_attr_id
        
        if res_attrs[ra_id].is_var == 'Y':
            continue # counterintuitively, this is not an input variable
        
        # get identifiers
        if ra_id in ra_node.keys():
            ftype = 'node'
            ID = ra_node[rs.resource_attr_id]
        elif ra_id in ra_link.keys():
            ftype = 'link'
            ID = link_nodes[ra_link[rs.resource_attr_id]]
        #elif ra_id in ra_net.keys():
            #ftype = 'net'
            #fid = ra_net[rs.resource_attr_id]        
        
        # initialize parameter dictionary
        param = res_attrs[ra_id].name.replace(' ', '_')
        if param not in p[ftype].keys():
            p[ftype][param] = {}
            
        # specify the dataset value
        value = rs.value.value
        
        # specify the feature type
        typ = rs.value.type
        
        metadata = json.loads(rs.value.metadata)
        
        # process the different data types
        idx = ID
        if typ == 'scalar':
            if type(idx) is list:
                idx = tuple(idx)
            p[ftype][param][idx] = float(value) # note: hydra stores scalars as strings
            
        elif typ == 'descriptor': # this could change later
            if type(idx) is list:
                idx = tuple(idx)
            p[ftype][param][idx] = value
            
        elif typ == 'timeseries':
            if type(ID) is not list:
                ID = [ID]
            values = json.loads(value)
            is_function = 'function' in metadata.keys() and len(metadata['function']) > 0
            for d, (ht, ot) in timestep_dict.items():
                if is_function:
                    value = eval_function(metadata['function'], d)
                else:
                    value = values['0'][ht]
                idx = tuple(ID + [ot])
                p[ftype][param][idx] = value

    # create model    
    model = create_model(model_name,
                         nodes,
                         links,
                         type_nodes,
                         type_links,
                         timesteps,
                         p)
    
    return model
