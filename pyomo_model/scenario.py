from os.path import join
from datetime import datetime
import json
from collections import OrderedDict
from attrdict import AttrDict

from pyomo.environ import ConcreteModel, Set, Objective, Var, Param, Constraint, NonNegativeReals, maximize, summation
from pyomo.opt import SolverFactory
from dateutil import rrule
from dateutil.parser import parse
from matplotlib import pyplot as plt

from utils import connection, create_logger, eval_function

import wingdbstub

def create_model(network, template, timestep_dict):
    
    # prepare data - we could move some of this to elsewhere

    template_id = template.id      
    
    # extract info about nodes
    
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
                
    # extract info about links
    
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
    
    # extract info about time steps
    
    timesteps = [ot for (ht, ot) in timestep_dict.values()]
    
    # initialize dictionary of parameters
    p = AttrDict({ft: AttrDict({}) for ft in ['node', 'link', 'net']})
    
    ra_node = {} # res_attr to node lookup
    for node in network.nodes:
        for res_attr in node.attributes:
            ra_node[res_attr.id] = node.id
    
    ra_link = {} # res_attr to link lookup
    for link in network.links:
        for res_attr in link.attributes:
            ra_link[res_attr.id] = link.id
            
    #ra_net = dict() # res_attr to network lookup
    #for link in network.links:
        #for res_attr in link.attributes:
            #ra_link[res_attr.id] = link.id
    
    for rs in network.scenarios[0].resourcescenarios:
        
        ra_id = rs.resource_attr_id
        
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
        param = rs.value.name.replace(' ', '_')
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

    # prepare model
    
    model = ConcreteModel(name = 'OpenAgua')
    
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
    model.Non_reservoir = model.Nodes - model.Reservoir
    
    # variables
    
    model.S = Var(model.Reservoir * model.TS, domain=NonNegativeReals) # storage
    model.Si = Var(model.Reservoir * model.TS, domain=NonNegativeReals) # initial storage
    model.D = Var(model.Non_reservoir * model.TS, domain=NonNegativeReals) # delivery
    model.I = Var(model.Nodes * model.TS, domain=NonNegativeReals) # inflow
    model.L = Var(model.Nodes * model.TS, domain=NonNegativeReals) # loss (outflow)
    model.Q = Var(model.Links * model.TS, domain=NonNegativeReals) # flow in links
    
    # paramters 
    
    def NodePriority_rule(model, j, t):
        priority = -1 # default 
        if 'Priority' in p.node.keys() and (j, t) in p.node['Priority'].keys():
            priority = p.node['Priority'][(j, t)]
        elif j in model.Outflow:
            priority = 0
        return priority
    model.Demand_Priority = Param(model.Non_reservoir, model.TS, rule=NodePriority_rule)
    model.Storage_Priority = Param(model.Reservoir, model.TS, rule=NodePriority_rule)
    
    def LinkPriority_rule(model, i, j, t):
        priority = 0
        if 'Priority' in p.link.keys() and (i, j, t) in p.link['Priority'].keys():
            priority = p.link['Priority'][(i, j, t)]
        return priority    
    model.Flow_Priority = Param(model.Links, model.TS, rule=LinkPriority_rule)
    
    # constraints
    
    def MassBalance_rule(model, j, t):
        if j in model.Reservoir:
            expr = model.Si[j, t] - model.S[j, t] + model.I[j, t] \
                + sum(model.Q[i,j,t] for i in model.NodesIn[j]) \
                - sum(model.Q[j,k,t] for k in model.NodesOut[j]) \
                - model.L[j, t] == 0
        else:
            expr = model.I[j, t] \
                + sum(model.Q[i,j,t] for i in model.NodesIn[j]) \
                - sum(model.Q[j,k,t] for k in model.NodesOut[j]) \
                - model.L[j, t] == 0
        return expr
    model.MassBalance = Constraint(model.Nodes, model.TS, rule=MassBalance_rule)
    
    def IntialStorage_rule(model, j, t):
        if t == model.TS.first():
            expr = model.Si[j, t] == p.node['Initial_Storage'][j]
        else:
            expr = model.Si[j, t] == model.S[j, model.TS.prev(t)]
        return expr
    model.IntialStorage = Constraint(model.Reservoir, model.TS, rule=IntialStorage_rule)
    
    def Delivery_rule(model, j, t):
        return model.D[j,t] == sum(model.Q[i,j,t] for i in model.NodesIn[j])
    model.Delivery = Constraint(model.Non_reservoir, model.TS, rule=Delivery_rule)
    
    def ChannelCap_rule(model, i, j, t):
        if 'Flow_Capacity' in p.link.keys() and (i,j,t) in p.link['Flow_Capacity'].keys():
            return (0, model.Q[i,j,t], p.link['Flow_Capacity'][(i,j,t)])
        else:
            return Constraint.Skip
    model.ChannelCapacity = Constraint(model.Links, model.TS, rule=ChannelCap_rule)

    def DeliveryCap_rule(model, j, t):
        if 'Demand' in p.node.keys() and (j,t) in p.node['Demand'].keys():
            return (0, model.D[j,t], p.node['Demand'][(j,t)])
        else:
            return Constraint.Skip
    model.DeliveryCap = Constraint(model.Non_reservoir, model.TS, rule=DeliveryCap_rule)
    
    def StorageBounds_rule(model, j, t):
        return (p.node['Inactive_Pool'][(j,t)], model.S[j,t], p.node['Storage_Capacity'][(j,t)])
    model.StorageBounds = Constraint(model.Reservoir, model.TS, rule=StorageBounds_rule)

    # boundary conditions
    
    def Inflow_rule(model, j, t):
        if 'Runoff' in p.node.keys() and (j,t) in p.node['Runoff'].keys():
            inflow = p.node['Runoff'][(j,t)]
        else:
            inflow = 0        
        return model.I[j,t] == inflow
    model.Inflow = Constraint(model.Nodes, model.TS, rule=Inflow_rule)
    
    def Loss_rule(model, j, t):
        if j in model.Outflow:
            expr = Constraint.Skip
        elif 'Consumptive_Loss' in p.node.keys() and (j,t) in p.node['Consumptive_Loss']:
            expr = model.L[j,t] == model.D[j,t] * p.node['Consumptive_Loss'][(j,t)] / 100
        else:
            expr = model.L[j,t] == 0
        return expr
    model.Loss = Constraint(model.Nodes, model.TS, rule=Loss_rule)

    # objective function

    def Objective_fn(model):
        expr = summation(model.Demand_Priority, model.D) \
            + summation(model.Storage_Priority, model.S) \
            + summation(model.Flow_Priority, model.Q)
        return expr
    model.Ojective = Objective(rule=Objective_fn, sense=maximize)

    return model

# run the the main scenario-specific routine
def run_scenario(scenario_id, args=None):

    scenario_id = 5 # get from args
    
    logfile = join(args.scenario_log_dir, 'scenario_{}.log'.format(scenario_id))
    log = create_logger(args.app_name, logfile)
    log.info('starting scenario {}'.format(scenario_id))
    
    # get connection, along with useful tools attached
    conn = connection(args, scenario_id, args.template_id, log)
    
    # time steps
    ti = datetime.strptime(args.initial_timestep, args.timestep_format)
    tf = datetime.strptime(args.final_timestep, args.timestep_format)
    dates = [date for date in rrule.rrule(rrule.MONTHLY, dtstart=ti, until=tf)]
    
    timestep_dict = OrderedDict()
    OAtHPt = {}
    for date in dates:
        oat = date.strftime(args.timestep_format)
        hpt = date.strftime(args.hydra_timestep_format)
        timestep_dict[date] = [hpt, oat]
        OAtHPt[oat] = hpt
    
    # create the model
    instance = create_model(conn.network, conn.template, timestep_dict)
    log.info('model created')
    opt = SolverFactory(args.solver)
    results = opt.solve(instance)
    log.info('model solved')
    
    # save results by updating the scenario
    res_scens = {}
    updated_res_scens = []
    for rs in conn.network.scenarios[0].resourcescenarios:
        res_scens[rs.resource_attr_id] = rs
        
    update_scenario = False

    for i, r in enumerate(instance.Reservoir):
        ra_id = conn.res_attrs.node[(r, 'storage')]
        attr_id = conn.attr_ids[ra_id]
        attr = conn.attrs.node[attr_id]
        indices = [(r, ts) for ts in instance.TS]
        timeseries = {}
        for index in indices:
            timeseries[OAtHPt[index[1]]] = instance.S[index].value
        timeseries = json.dumps({'0': timeseries})
            
        if ra_id not in res_scens.keys():
            # create a new dataset
            dataset = {
                'type': attr.dtype,
                'name': 'Storage for {}'.format(attr.name),
                'unit': attr.unit,
                'dimension': attr.dim,
                'value': timeseries
            }            
            conn.call('add_data_to_attribute',
                      {'scenario_id': scenario_id, 'resource_attr_id': ra_id, 'dataset': dataset})
        else:
            # just update the existing resourcedata
            dataset = res_scens[ra_id].value
            dataset.value = timeseries
            updated_res_scen = {
                'resource_attr_id': ra_id,
                'attr_id': attr_id,
                'value': dataset
            }
            updated_res_scens.append(json.dumps(updated_res_scen))
            
    if updated_res_scens:
        update = conn.call('update_resourcedata',
                           {'scenario_id': scenario_id, 'resource_scenarios': updated_res_scens})
    
    log.info('model results saved')
    
    # ===========================
    # start the per timestep loop
    # ===========================
   
    #T = len(dates)
    #for t, date in enumerate(dates):
        
        # ===========================
        # prepare the time steps to use in the optimization run
        # ===========================        

        # ===========================
        # prepare the inflow forecast model
        # ===========================

        # For now, forecast based on mean monthly inflow at each catchment node
        # However, this can be changed in the future

        # ===========================
        # run the model
        # ===========================
        
        #if new_model:
            #model = create_model(data)
            #instance = model.create_instance()            
        #else:
            #instance = update_instance(instance, S0, inflow)
            #instance.preprocess()
            
        # solve the model
        #results = solver.solve(instance)
        
        # load the results
        #instance.solutions.load_from(results)
        
        # set initial conditions for the next time step
        #S0 = instance.S[isIDs[0]].value
        #if S0 is None:
            #S0 = 0.0
            
        # ===========================
        # save results to memory
        # ===========================
        
        
        #log.info('completed timestep {} | {}/{}'.format(dt.date.strftime(date, args.timestep_format), t+1, T))
    
    # ===========================
    # save results to Hydra Server
    # ===========================
    
    
    return
