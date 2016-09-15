from pyomo.core import *

from model import create_model, update_instance
from os.path import join

from utils import connection
from utils import create_logger

import wingdbstub

# run the the main scenario-specific routine
def run_scenario(scenario, args=None):
    
    logfile = join(args.scenario_log_dir, 'scenario_{}.log'.format(scenario))
    log = create_logger(args.app_name, logfile)
    log.info('starting scenario {}'.format(scenario))    

    # specify scenario-level parameters parameters (this are sent via params)
    try:
        log.info('creating timesteps')
        ti = dt.datetime.strptime(args.initial_timestep, args.timestep_format)
        tf = dt.datetime.strptime(args.final_timestep, args.timestep_format)
        dates = [date for date in rrule.rrule(rrule.MONTHLY,
                                              dtstart=ti, until=tf)]
    except:
        log.info('failed to create timesteps with args: {}'.format(args))
    finally:
        log.info('failed to create timesteps')    
    log.info('running scenario {} for {} months: {} to {}'
             .format(scenario,
                     len(dates),
                     args.initial_timestep,
                     args.final_timestep))

    # ===========================
    # load scenario data
    # ===========================
   
    #conn.

    # ===========================
    # create the optimization solver
    # ===========================

    #solver = SolverFactory(args.solver)
   
    # ===========================
    # start the per timestep loop
    # ===========================
   
    T = len(dates)
    for t, date in enumerate(dates):
        
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
        
        
        log.info('completed timestep {} | {}/{}'.format(dt.date.strftime(date, args.timestep_format), t+1, T))
    
    # ===========================
    # save results to Hydra Server
    # ===========================
    
    
    return
