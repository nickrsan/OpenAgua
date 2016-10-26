import json

from pyomo.environ import ConcreteModel, Set, Objective, Var, Param, Constraint, NonNegativeReals, maximize, summation
from attrdict import AttrDict

from utils import eval_function

def create_model(model_name, nodes, links, type_nodes, type_links, timesteps, p):

    m = ConcreteModel(name = model_name)
    
    # SETS
    
    # basic sets
    m.Nodes = Set(initialize=nodes) # nodes
    m.Links = Set(initialize=links) # links
    m.TS = Set(initialize=timesteps, ordered=True) # time steps
    
    # all nodes directly upstream from a node
    def NodesIn_init(m, node):
        retval = []
        for (i,j) in m.Links:
            if j == node:
                retval.append(i)
        return retval
    m.NodesIn = Set(m.Nodes, initialize=NodesIn_init)
    
    # all nodes directly downstream from a node
    def NodesOut_init(m, node):
        retval = []
        for (j,k) in m.Links:
            if j == node:
                retval.append(k)
        return retval
    m.NodesOut = Set(m.Nodes, initialize=NodesOut_init)    
    
    # create sets (nodes or links) for each template type
    for k, v in type_nodes.items():
        exec('m.{} = Set(within=m.Nodes, initialize={})'.format(k, v))
    for k, v in type_links.items():
        exec('m.{} = Set(within=m.Links, initialize={})'.format(k, v))
    
    # create set for non-storage nodes
    m.NonReservoir = m.Nodes - m.Reservoir
    m.Demand_Nodes = m.NonReservoir - m.Junction
    
    # VARIABLES
    
    m.S = Var(m.Reservoir * m.TS, domain=NonNegativeReals) # storage
    m.D = Var(m.Demand_Nodes * m.TS, domain=NonNegativeReals) # delivery to demand nodes
    
    m.G = Var(m.Nodes * m.TS, domain=NonNegativeReals) # gain (local inflow)
    m.L = Var(m.Nodes * m.TS, domain=NonNegativeReals) # loss (local outflow)
    m.I = Var(m.Nodes * m.TS, domain=NonNegativeReals) # total inflow to a node
    m.O = Var(m.Nodes * m.TS, domain=NonNegativeReals) # total outflow from a node
    m.Q = Var(m.Links * m.TS, domain=NonNegativeReals) # flow in links
    
    # PARAMETERS 
    
    def InitialStorage(m, j):
        return p.node['Initial_Storage'][j]
    m.Si = Param(m.Reservoir, rule=InitialStorage)
    
    def NodePriority_rule(m, j, t):
        if j in m.Outflow:
            return 0
        elif 'Priority' in p.node.keys() and (j, t) in p.node['Priority'].keys():
            return p.node['Priority'][(j, t)]
        else:
            return -1
    m.Demand_Priority = Param(m.Demand_Nodes, m.TS, rule=NodePriority_rule)
    m.Storage_Priority = Param(m.Reservoir, m.TS, rule=NodePriority_rule)

    def LinkPriority_rule(m, i, j, t):
        if (i,j) in m.River:
            return 0
        elif 'Priority' in p.link.keys() and (i, j, t) in p.link['Priority'].keys():
            return p.link['Priority'][(i, j, t)]
        else:
            return -1
    m.Flow_Priority = Param(m.Links, m.TS, rule=LinkPriority_rule)
    
    # CONSTRAINTS
    
    def Inflow_rule(m, j, t): # not to be confused with Inflow resources
        return m.I[j,t] == sum(m.Q[i,j,t] for i in m.NodesIn[j])
    m.Inflow_definition = Constraint(m.Nodes, m.TS, rule=Inflow_rule)
    
    def Outflow_rule(m, j, t): # not to be confused with Outflow resources
        return m.O[j,t] == sum(m.Q[j,k,t] for k in m.NodesOut[j])
    m.Outflow_definition = Constraint(m.Nodes, m.TS, rule=Outflow_rule)
    
    def Delivery_rule(m, j, t): # basically the same as I, but for a different purpose
        return m.D[j,t] == sum(m.Q[i,j,t] for i in m.NodesIn[j])
    m.Delivery_definition = Constraint(m.Demand_Nodes, m.TS, rule=Delivery_rule)
    
    def MassBalance_rule(m, j, t):
        if j in m.Reservoir:
            if t == m.TS.first():
                return m.S[j, t] - m.Si[j] == m.G[j, t] + m.I[j,t] - m.L[j, t] - m.O[j,t]
            else:
                return m.S[j, t] - m.S[j, m.TS.prev(t)] == m.G[j, t] + m.I[j,t] - m.L[j, t] - m.O[j,t]
        else:
            return m.G[j, t] + m.I[j,t] == m.L[j, t] + m.O[j,t]
    m.MassBalance = Constraint(m.Nodes, m.TS, rule=MassBalance_rule)
    
    def ChannelCap_rule(m, i, j, t):
        if (i,j) in m.River:
            return Constraint.Skip
        elif (i,j) in m.Return_Flow:
            return Constraint.Skip
        elif 'Flow_Capacity' in p.link.keys() and (i,j,t) in p.link['Flow_Capacity'].keys():
            return (0, m.Q[i,j,t], p.link['Flow_Capacity'][(i,j,t)])
        else:
            return (0, m.Q[i,j,t], 0) # default flow capacity is zero
    m.ChannelCapacity = Constraint(m.Links, m.TS, rule=ChannelCap_rule)
    
    # NB: delivery should be constrained by delivery link capacity, not actual demand, which
    # will be driven by economics
    def DeliveryCap_rule(m, j, t):
        if 'Demand' in p.node.keys() and (j,t) in p.node['Demand'].keys():
            return m.D[j,t] <= p.node['Demand'][(j,t)]
        else:
            return Constraint.Skip
    m.DeliveryCap = Constraint(m.Demand_Nodes, m.TS, rule=DeliveryCap_rule)
    
    def StorageBounds_rule(m, j, t):
        return (p.node['Inactive_Pool'][(j,t)], m.S[j,t], p.node['Storage_Capacity'][(j,t)])
    m.StorageBounds = Constraint(m.Reservoir, m.TS, rule=StorageBounds_rule)
    
    # boundary conditions
    
    # this will be expanded significantly
    def LocalGain_rule(m, j, t):
        if 'Runoff' in p.node.keys() and (j,t) in p.node['Runoff'].keys():
            return m.G[j,t] == p.node['Runoff'][(j,t)]
        else:
            return m.G[j,t] == 0 # no local gain
    m.Local_Gain = Constraint(m.Nodes, m.TS, rule=LocalGain_rule)
    
    # this will also be expanded to account for loss to groundwater, etc.
    def LocalLoss_rule(m, j, t):
        if j in m.Outflow: # no constraint at outflow nodes
            return Constraint.Skip
        elif 'Consumptive_Loss' in p.node.keys() and (j,t) in p.node['Consumptive_Loss']:
            return m.L[j,t] == m.D[j,t] * p.node['Consumptive_Loss'][(j,t)] / 100
        else:
            return m.L[j,t] == 0 # no local loss
    m.Local_Loss = Constraint(m.Nodes, m.TS, rule=LocalLoss_rule)
    
    # OBJECTIVE FUNCTION
    
    def Objective_fn(m):
        return summation(m.Demand_Priority, m.D) + summation(m.Storage_Priority, m.S) + summation(m.Flow_Priority, m.Q)
    m.Ojective = Objective(rule=Objective_fn, sense=maximize)
    
    return m


def prepare_model(model_name, network, template, attr_names, timestep_dict):
    
    # prepare data - we could move some of this to elsewhere 
    
    template_id = template.id
    
    # extract info about nodes & links
    
    nodes = []   
    links = []
    res_attrs = {}
    link_nodes = {}
    type_nodes = {tt.name.replace(' ', '_'): [] for tt in template.types if tt.resource_type == 'NODE'}
    type_links = {tt.name.replace(' ', '_'): [] for tt in template.types if tt.resource_type == 'LINK'}
    
    # NODES
    for n in network.nodes:
        
        # a list of all nodes
        nodes.append(n.id)
        
        # a dictionary of template_type to node_id
        for t in n.types:
            if t.template_id == template_id:
                type_nodes[t.name.replace(' ', '_')].append(n.id)
            
        # general resource attribute information    
        for ra in n.attributes:
            res_attrs[ra.id] = AttrDict({'name': attr_names[ra.attr_id], 'is_var': ra.attr_is_var})           
                
    # LINKS
    for l in network.links:
        node_ids = [l.node_1_id, l.node_2_id]
        
        # a list of all links
        links.append(tuple(node_ids))
        
        # a dictionary of link_id to [node_1_id, node_2_id]
        link_nodes[l.id] = node_ids
        
        # a dictionary of template type to [node_1_id, node_2_id]
        for t in l.types:
            if t.template_id == template_id:
                type_links[t.name.replace(' ', '_')].append(tuple(node_ids))
        
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
    model = create_model(model_name, nodes, links, type_nodes, type_links, timesteps, p)
    
    return model
