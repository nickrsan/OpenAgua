# import
import pandas
from pandas.io.json import json_normalize
import sys
import json

# multicore processing tools
import multiprocessing as mp
from functools import partial
poolsize = mp.cpu_count()

from ..connection import connection

# run the model
# session holds all constant settings
# scenario simply specifies which scenario to run
def run_model(session, scenario):
    pass

def main(session, scenario_sets):

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
    
    pool = mp.Pool(processes=poolsize, maxtasksperchild=1)
    
    # set up the partial function with non-variable parameters as session (p in run_model)
    f = partial(run_model, p=session)
    
    # pass partial to pools with scenario-specific data as scenarios (s in run_model)
    # scenarios should be defined from scenario sets, passed by user
    pools = pool.imap(f, scenarios, chunksize=session['chunksize'])
    
    # iterate over results
    for result in enumerate(pools):
        
        # log progress
        #log...
               
        # save results 
        if result is not None:
            # add results to Hydra via json
            pass
        
        else:
            # log(...)
            pass
                 
    # stop the pool
    pool.close()
    pool.join()
    pbar.finish()

#def run_from_file(datafile):
    
if __name__=='__main__':
    run_from_file("input.dat") # useful for testing (but not ready)
    
