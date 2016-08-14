# import

import argparse as ap

from connection import connection

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
            
# the main per time step routine
def run_timestep(data):
    
    return 5

# run the the main scenario-specific routine
# params holds all constant settings
# scenario simply specifies which Hydra scenario to run
def run_scenario(args, scenario):
    
    # log in to Hydra Platform
    #conn = connection(url)
    #if session_id is not None:
        #conn.session_id=session_id
    #else:
        #conn.login()
    
    #project = args['project']
    
    ## set up the log file
    #logfile = 'status - {project} - {scenario}.log'.format(project=project, scenario=scenario)
    #logging.basicConfig(filename=join('log', logfile), level=logging.INFO)
    
    ## specify scenario-level parameters parameters (this are sent via params)
    ti = args.initial_timestep
    tf = args.final_timestep
    print('ti: %s, tf: %s' % (ti, tf))
    
    #timesteps = range(10)
    #for ts in timesteps:
        
        ## main per scenario modeling routine here
        #data = ts
        
        #run_timestep(data)
        
        #sleep(1)
        #msg = '{}'.format(ts)
        #logging.info(msg)

def run_scenarios(args):
    """
        This is a wrapper for running all the scenarios, where scenario runs are
        processor-independent.
    """

    # do any one-time processing here

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
    
    # set multiprocessing parameters
    poolsize = mp.cpu_count()
    maxtasks = 1    
    
    # log start of run
    #log('Running in multicore mode with pool.{}: {} workers, {} chunks each.' \
          #.format(session['pooltype'], poolsize, session['chunksize]))
    
    pool = mp.Pool(processes=poolsize, maxtasksperchild=maxtasks)
    
    # set up the partial function with non-variable parameters as session (p in run_model)
    f = partial(run_scenario, args=args)
    
    # pass partial to pools with scenario-specific data as scenarios (s in run_model)
    # scenarios should be defined from scenario sets, passed by user
    pools = pool.imap(f, eval(args.scids), chunksize=chunksize)
    
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
                 
    #stop the pool
    pool.close()
    pool.join()
    pbar.finish()
    
def commandline_parser():
    """
        Parse the arguments passed in from the command line.
    """
    parser = ap.ArgumentParser(
        description="""Run the OpenAgua pyomo optimization model.
                    Written by David Rheinheimer <david.rheinheimer@gmail.com>
                    (c) Copyright 2016, Tecnologico de Monterrey.
        """, epilog="For more information visit www.openaguadss.org",
       formatter_class=ap.RawDescriptionHelpFormatter)

    parser.add_argument('-url', '--server-url',
                        help='''The Hydra Server URL.''')
    parser.add_argument('-sid', '--session-id',
                        help='''The Hydra Server session ID. Will be created from
                        the config info if not provided.''')
    parser.add_argument('-nid', '--network-id',
                        help='''The network ID of the model to be run.''')
    parser.add_argument('-tid', '--template-id',
                        help='''The template ID of the model to be run.''')
    parser.add_argument('-scids', '--scenario-ids',
                        help='''The scenario IDs of the scenarios to be run,
                        specified as a string containing a comma-separated list of
                        integers. If no IDs are specified, all scenarios asscoiated
                        with the network/template will be run.
                        ''')
    parser.add_argument('-ti', '--initial-timestep',
                        help='''The first timestep of the model.''')
    parser.add_argument('-tf', '--final-timestep',
                        help='''The final timestep of the model.''')
    parser.add_argument('-log', '--logfile-dir',
                        help='''The log file directory. Default is "./log"''')
    return parser    
    
if __name__=='__main__':
    
    parser = commandline_parser()
    args = parser.parse_args()
    
    print(args)
    
    # pull out args from scenarios
    
    run_scenarios(args)