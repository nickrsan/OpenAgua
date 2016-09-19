from os.path import join
from datetime import datetime
import json
from collections import OrderedDict

from pyomo.environ import *
from pyomo.opt import SolverFactory
from dateutil import rrule
from dateutil.parser import parse

from model import update_instance
from utils import connection, create_logger, eval_function

import wingdbstub

def create_model(network, template_id, timestep_dict):
    
    # prepare data
    
    nodes =[n.id for n in network.nodes]
    links = [(l.node_1_id, l.node_2_id) for l in network.links]
    
    timesteps = [ot for (ht, ot) in timestep_dict.values()]
    
    res_attr_node = dict()
    for node in network.nodes:
        for res_attr in node.attributes:
            res_attr_node[res_attr.id] = node.id
    
    p = dict() # dictionary of parameters
    
    for rs in network.scenarios[0].resourcescenarios:
        param = rs.value.name.replace(' ','_')
        if param not in p.keys():
            p[param] = dict()
        node_id = res_attr_node[rs.resource_attr_id]
        value = rs.value.value
        typ = rs.value.type
        metadata = json.loads(rs.value.metadata)
        if typ == 'scalar':
            exec('p["{}"][{}] = {}'.format(param, node_id, value))
        elif typ == 'descriptor':
            exec('p["{}"][{}] = {}'.format(param, node_id, value))
        elif typ == 'timeseries':
            values = json.loads(value)
            is_function = 'function' in metadata.keys() \
                and len(metadata['function']) > 0
            for d, (ht, ot) in timestep_dict.items():
                if is_function:
                    value = eval_function(metadata['function'], d)
                else:
                    value = values['0'][ht]
                exec('p["{}"][({},"{}")] = value'.format(param, node_id, ot))

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
    
    # get a list of all nodes of a given type
    type_nodes = dict()
    for n in network.nodes:
        for t in n.types:
            if t.template_id == template_id:
                type_name = t.name.replace(' ', '_')
                if type_name not in type_nodes.keys():
                    type_nodes[type_name] = []
                type_nodes[type_name].append(n.id)
                
    # create sets for each template type
    for k, v in type_nodes.items():
        exec('model.{} = Set(within=model.Nodes, initialize={})'.format(k, v))
    
    # create set for non-storage nodes
    model.Non_reservoir = model.Nodes - model.Reservoir
    
    # variables
    
    model.S = Var(model.Reservoir * model.TS, domain=NonNegativeReals) # storage
    model.Si = Var(model.Reservoir * model.TS, domain=NonNegativeReals) # initial storage
    model.D = Var(model.Non_reservoir * model.TS, domain=NonNegativeReals) # delivery
    model.I = Var(model.Nodes * model.TS, domain=NonNegativeReals) # inflow
    model.L = Var(model.Nodes * model.TS, domain=NonNegativeReals) # loss (outflow)
    model.Q = Var(model.Links * model.TS, domain=NonNegativeReals) # flow in links
       
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
        if t==model.TS.first():
            return model.Si[j, t] == p['Initial_Storage'][j]
        else:
            return model.Si[j, t] == model.S[j, model.TS.prev(t)]
    model.IntialStorage = Constraint(model.Reservoir, model.TS, rule=IntialStorage_rule)
    
    def Delivery_rule(model, j, t):
        return model.D[j,t] == sum(model.Q[i,j,t] for i in model.NodesIn[j])
    model.Delivery = Constraint(model.Non_reservoir, model.TS, rule=Delivery_rule)
    
    def ChannelCap_rule(model, i, j, t):
        if 'Flow_Capacity' in p.keys() and (i,j) in p['Flow_Capacity'].keys():
            return (model.Q[i,j,t], p['Flow_Capacity'][(i,j,t)])
        else:
            return Constraint.Skip
    model.ChannelCapacity = Constraint(model.Links, model.TS, rule=ChannelCap_rule)
    
    def MinStorage_rule(model, j, t):
        return (p['Inactive_Pool'][(j,t)], model.S[j,t])
    model.MinStorage = Constraint(model.Reservoir, model.TS, rule=MinStorage_rule)

    def MaxStorage_rule(model, j, t):
        return (model.S[j,t], p['Storage_Capacity'][(j,t)])
    model.MaxStorage = Constraint(model.Reservoir, model.TS, rule=MaxStorage_rule)
    
    # boundary conditions
    
    def Inflow_rule(model, j, t):
        if 'Runoff' in p.keys() and (j,t) in p['Runoff'].keys():
            return (0, model.I[j,t] - p['Runoff'][j,t], 0)
        else:
            return (0, model.I[j,t], 0)
    model.Inflow = Constraint(model.Nodes, model.TS, rule=Inflow_rule)
    
    def Loss_rule(model, j, t):
        if j in model.Outflow:
            expr = Constraint.Skip
        elif 'Consumptive_Loss' in p.keys() and (j,t) in p['Consumptive_Loss']:
            expr = model.L[j,t] \
                == model.D[j,t] * p['Consumptive_Loss'][(j,t)] / 100
        else:
            expr = model.L[j,t] == 0
        return expr
    model.Loss = Constraint(model.Nodes, model.TS, rule=Loss_rule)

    # objective function

    def OBJ_rule(model, j, t):
        if 'Priority' in p.keys() and (j, t) in p['Priority'].keys():
            priority = p['Priority'][(j, t)]
        else:
            priority = -1 # default
        if j in model.Reservoir:
            expr = priority * model.S[j, t]
        else:
            if j in model.Outflow:
                priority = 0
            expr = priority * model.D[j, t]

        return expr
    model.OBJ = Objective(model.Nodes, model.TS, rule=OBJ_rule, sense=maximize)

    return model

# run the the main scenario-specific routine
def run_scenario(scenario_id, args=None):
    
    logfile = join(args.scenario_log_dir, 'scenario_{}.log'.format(scenario_id))
    log = create_logger(args.app_name, logfile)
    log.info('starting scenario {}'.format(scenario_id))
    
    # get connection
    conn = connection(args, scenario_id, log)    
    
    # time steps
    ti = datetime.strptime(args.initial_timestep, args.timestep_format)
    tf = datetime.strptime(args.final_timestep, args.timestep_format)
    dates = [date for date in rrule.rrule(rrule.MONTHLY, dtstart=ti, until=tf)]
    
    timestep_dict = OrderedDict()
    for date in dates:
        oat = date.strftime(args.timestep_format)
        hpt = date.strftime(args.hydra_timestep_format)
        timestep_dict[date] = [hpt, oat]
    
    # create the model
    model = create_model(conn.network, args.template_id, timestep_dict)
    log.info('model created')
    
    # create the solver
    #stream_solver = True     # True prints solver output to screen
    #keepfiles =     False    # True prints intermediate file names (.nl,.sol,...)    
    opt = SolverFactory(args.solver)
    
    # solve the model
    results = opt.solve(model)
    log.info('model solved')

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
