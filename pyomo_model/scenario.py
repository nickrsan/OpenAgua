from io import StringIO
import sys

from os.path import join
from datetime import datetime
import json
from collections import OrderedDict
from attrdict import AttrDict

from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
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
                         msg_format='%(asctime)s - %(message)s')
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
    conn.OAtHPt = {}
    for date in dates:
        oat = date.strftime(args.timestep_format)
        hpt = date.strftime(args.hydra_timestep_format)
        timestep_dict[date] = [hpt, oat]
        conn.OAtHPt[oat] = hpt
        
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
    results = opt.solve(instance, tee=False)
    #logd.info('model solved')

    old_stdout = sys.stdout
    sys.stdout = summary = StringIO()
    results.write()
    sys.stdout = old_stdout
    
    logd.info('model solved\n' + summary.getvalue())
    
    if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
        # this is feasible and optimal
        logd.info('Optimal feasible solution found.')
        #outputnames = {'S': 'storage', 'I': 'inflow', 'O': 'outflow'}
        outputnames = {'I': 'inflow', 'O': 'outflow'}
        conn.save_results(instance, outputnames)
        logd.info('Results saved.')
    elif results.solver.termination_condition == TerminationCondition.infeasible:
        logd.info('WARNING! Problem is infeasible. Check detailed results.')
        # do something about it? or exit?
    else:
        # something else is wrong
        logd.info('WARNING! Something went wrong. Likely the model was not built correctly.')    
    
    # Still we will report that the model is complete...
    if args.foresight == 'perfect':
        msg = 'completed timesteps {} - {} | 1/1'.format(ti, tf)
        logd.info(msg)
        logp.info(msg)
    
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
