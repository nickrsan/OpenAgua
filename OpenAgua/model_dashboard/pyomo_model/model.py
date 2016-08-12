# import
import pandas
from pandas.io.json import json_normalize
import os
import sys
import json
from time import sleep
import logging

# multicore processing tools
import multiprocessing as mp
from functools import partial
poolsize = mp.cpu_count()

#from ..connection import connection

def run_timestep(data):
    return 5

# run the model
# params holds all constant settings
# scenario simply specifies which Hydra scenario to run
def run_model(params, scenario):
    project = params['project']
    logfile = 'status - {project} - {scenario}.log'.format(project=project, scenario=scenario)
    logging.basicConfig(filename=join('log', logfile), level=logging.INFO)
    t0, tf = params['start'], params['finish']
    timesteps = range(10)
    for ts in timesteps:
        
        data = ts
        
        run_timestep(data)
        
        #sleep(0.01)
        msg = '{}'.format(ts)
        logging.info(msg)         

def get_progress(by_timestep, timesteps_count = None):
    completed = 0
    for fname in os.listdir('./log'):
        n = len(open(fname).readlines())
        if by_timestep:
            completed += n
        else:
            if n == timesteps_count:
                completed += 1
    return completed

def main(params, scenarios, chunksize):

    # =====
    # input
    # =====
    
    # general parameters
    
    # ===============================
    # initializations & preprocessors
    # ===============================
    
    # ==============================
    # hydrologic info pre-processing
    # ==============================
    
        
    # ============
    # create model
    # ============
  

    # =============
    # run scenarios
    # =============
    
    # set up the scenarios based on scenario_sets
        
    # ==================
    # multi core routine
    # ==================
    
    # log start of run
    #log('Running in multicore mode with pool.{}: {} workers, {} chunks each.' \
          #.format(session['pooltype'], poolsize, session['chunksize]))
    poolsize = 1
    #pool = mp.Pool(processes=poolsize, maxtasksperchild=1)
    
    # set up the partial function with non-variable parameters as session (p in run_model)
    #f = partial(run_model, params=params)
    
    # pass partial to pools with scenario-specific data as scenarios (s in run_model)
    # scenarios should be defined from scenario sets, passed by user
    #pools = pool.imap(f, scenarios, chunksize=chunksize)
    
    # iterate over results
    #for result in enumerate(pools):
        
        ## log progress
        ##log...
               
        ## save results 
        #if result is not None:
            ## add results to Hydra via json
            #pass
        
        #else:
            ## log(...)
            #pass
                 
    # stop the pool
    #pool.close()
    #pool.join()
    #pbar.finish()
    
if __name__=='__main__':
    run_timestep("input.dat") # useful for testing one time step
    
