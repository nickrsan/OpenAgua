from os.path import join
from datetime import datetime
import json
from collections import OrderedDict
from attrdict import AttrDict

from pyomo.opt import SolverFactory
from pyomo.environ import Var
from dateutil import rrule
#from dateutil.parser import parse
from matplotlib import pyplot as plt

from model import prepare_model
from utils import connection, create_logger

import wingdbstub

# run the the main scenario-specific routine
def run_scenario(scenario_id, args=None):
    
    logd = create_logger(appname='{} - {} - details'.format(args.app_name, scenario_id),
                         logfile=join(args.scenario_log_dir,'scenario_{}_details.txt'.format(scenario_id)),
                         msg_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logp = create_logger(appname='{} - {} - progress'.format(args.app_name, scenario_id),
                         logfile=join(args.scenario_log_dir, 'scenario_{}_progress.txt'.format(scenario_id)),
                         msg_format='%(asctime)s - %(message)s')
    
    logd.info('starting scenario {}'.format(scenario_id))
    
    # get connection, along with useful tools attached
    conn = connection(args, scenario_id, args.template_id, logd)
    
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
        
    template_attributes = conn.call('get_template_attributes', {'template_id': conn.template.id})
    attr_names = {}
    for ta in template_attributes:
        attr_names[ta.id] = ta.name
        
    # create the model
    instance = prepare_model(model_name='OpenAgua',
                             network=conn.network,
                             template=conn.template,
                             attr_names=attr_names,
                             timestep_dict=timestep_dict)
    
    logd.info('model created')
    opt = SolverFactory(args.solver)
    results = opt.solve(instance)
    logd.info('model solved')
    
    # save results by updating the scenario
    res_scens = {}
    updated_res_scens = []
    for rs in conn.network.scenarios[0].resourcescenarios:
        res_scens[rs.resource_attr_id] = rs
        
    update_scenario = False
    
    outputnames = {'S': 'storage', 'I': 'inflow', 'O': 'outflow'}
    
    # loop through all the model variables
    for i, v in enumerate(instance.component_objects(Var, active=True)):
        varname = str(v)
        
        # continue if we aren't interested in this variable (intermediaries...)
        if varname not in outputnames.keys():
            continue
        
        fullname = outputnames[varname]
        
        # the variable object
        varobject = getattr(instance, varname)
        timeseries = {}
        
        # loop through all indices - including all nodes/links and timesteps
        for index in varobject:
            if len(index) == 2:
                idx = (index[0], fullname)
            else:
                idx = (index[0], index[1], fullname)
            if idx not in timeseries.keys():
                timeseries[idx] = {}
            timeseries[idx][OAtHPt[index[1]]] = varobject[index].value
    
        # save variable data to database
        for idx in timeseries.keys():
            
            ra_id = conn.res_attrs.node[idx]
            attr_id = conn.attr_ids[ra_id]
            attr = conn.attrs.node[attr_id]
            res_name = conn.res_names[ra_id]
            dataset_name = '{} for {}'.format(fullname, res_name)
            
            dataset_value = json.dumps({'0': timeseries[idx]})
            #dataset_value = {'0': timeseries[idx]}
            
            #if ra_id not in res_scens.keys():
                ## create a new dataset
            dataset = {
                'type': attr.dtype,
                'name': dataset_name,
                'unit': attr.unit,
                'dimension': attr.dim,
                'value': dataset_value
            }
            conn.call('add_data_to_attribute',
                      {'scenario_id': scenario_id, 'resource_attr_id': ra_id, 'dataset': dataset})
            #else:
                ## just update the existing resourcedata
                #rs = res_scens[ra_id]
                ##dataset = res_scens[ra_id].value
                #rs.value.name = dataset_name
                #rs.value.value = dataset_value
                ##updated_res_scen = {
                    ##'resource_attr_id': ra_id,
                    ##'attr_id': attr_id,
                    ##'value': dataset
                ##}
                #updated_res_scens.append(rs)

    #if updated_res_scens:
        #update = conn.call('update_resourcedata',
                           #{'scenario_id': scenario_id, 'resource_scenarios': updated_res_scens})
    
    logd.info('model results saved')
    
    if args.foresight == 'perfect':
        logp.info('completed timesteps {} - {} | 1/1'.format(ti, tf))
    
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
        
        
        #logd.info('completed timestep {} | {}/{}'.format(dt.date.strftime(date, args.timestep_format), t+1, T))
    
    # ===========================
    # save results to Hydra Server
    # ===========================
    
    
    return
