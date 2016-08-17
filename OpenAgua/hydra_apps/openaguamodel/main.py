# import
import argparse as ap

import logging
import os, sys
from os.path import join
from shutil import rmtree
from time import sleep

# hydra server connection
from connection import connection

# multicore processing tools
import multiprocessing
from functools import partial

# modeling
import datetime as dt
from dateutil import rrule
from scenario import run_scenario

# the main per time step routine
def run_timestep(data):
    
    return 5

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
    poolsize = multiprocessing.cpu_count()
    maxtasks = 1
    chunksize = 1
    
    pool = multiprocessing.Pool(processes=poolsize, maxtasksperchild=maxtasks)
    
    # run the model
    scenarios = eval(args.scenario_ids)
    
    log.info('Running {} scenarios in multicore mode with {} workers, {} chunks each.' \
             .format(len(scenarios), poolsize, chunksize))  
    pools = pool.imap(partial(run_scenario, args=args), scenarios, chunksize=chunksize)
    
    # iterate over results
    #for result in enumerate(pools):
        
        # log progress
        #log.info('finished pool')
                 
    #stop the pool
    pool.close()
    pool.join()
    
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

    parser.add_argument('-app', '--app-name',
                        help='''Name of the app.''')
    parser.add_argument('-url', '--hydra-url',
                        help='''The Hydra Server URL.''')
    parser.add_argument('-user', '--hydra-username',
                        help='''The username for logging in to Hydra Server.''')
    parser.add_argument('-pw', '--hydra-password',
                        help='''The password for logging in to Hydra Server.''')
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
    parser.add_argument('-tsf', '--timestep-format',
                        help='''The format of the timestep (e.g., as found on http://strftime.org).''')
    parser.add_argument('-log', '--log-dir',
                        help='''The main log file directory.''')
    parser.add_argument('-slog', '--scenario-log-dir',
                        help='''The log file directory for the scenarios.''')
    parser.add_argument('-sol', '--solver',
                        help='''The solver to use (e.g., glpk, gurobi, etc.).''')
    return parser

def create_logger(appname, logfile):
    logger = logging.getLogger(appname)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger
    
if __name__=='__main__':
    
    parser = commandline_parser()
    args = parser.parse_args()
    
    here = os.path.abspath(os.path.dirname(__file__))
    if args.log_dir is None:
        args.log_dir = '.'
    args.log_dir = os.path.join(here, args.log_dir)
        
    if args.scenario_log_dir is None:
        args.scenario_log_dir = 'logs'
    args.scenario_log_dir = os.path.join(here, args.scenario_log_dir)

    logfile = join(args.log_dir, 'log.log')
    log = create_logger(args.app_name, logfile)
        
    log.info('started model run with args: %s' % str(args))
    
    # delete old scenario log files
    for fname in os.listdir(args.scenario_log_dir):
        os.remove(join(args.scenario_log_dir, fname))
    
    run_scenarios(args)