import argparse
import os
from os.path import join
import shutil
import multiprocessing
from functools import partial
from pyomo.core import *

from scenario import run_scenario
from utils import create_logger, connection

import wingdbstub

def run_scenarios(args, log):
    """
        This is a wrapper for running all the scenarios, where scenario runs are
        processor-independent. As much of the Pyomo model is created here as
        possible.
    """
    
    # ==================
    # multi core routine
    # ==================
    
    # set multiprocessing parameters
    poolsize = multiprocessing.cpu_count()
    maxtasks = 1
    chunksize = 1
    
    pool = multiprocessing.Pool(processes=poolsize, maxtasksperchild=maxtasks)
    
    # run the model
    scenario_ids = args.scenario_ids
    p = partial(run_scenario, args=args)
    
    log.info('Running {} scenarios in multicore mode with {} workers, {} chunks each.' \
             .format(len(scenario_ids), poolsize, chunksize))  
    pools = pool.imap(p, scenario_ids, chunksize=chunksize)
    
    # iterate over results
    #for result in enumerate(pools):
        
        # log progress
        #log.info('finished pool')
                 
    #stop the pool
    pool.close()
    pool.join()
    return
    
def commandline_parser():
    """
        Parse the arguments passed in from the command line.
    """
    parser = argparse.ArgumentParser(
        description="""Run the OpenAgua pyomo optimization model.
                    Written by David Rheinheimer <david.rheinheimer@gmail.com>
                    (c) Copyright 2016, Tecnologico de Monterrey.
        """, epilog="For more information visit www.openagua.org",
       formatter_class=argparse.RawDescriptionHelpFormatter)

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
    parser.add_argument('-uid', '--user-id',
                        help='''The Hydra Server user_id.''')
    parser.add_argument('-nid', '--network-id',
                        help='''The network ID of the model to be run.''')
    parser.add_argument('-tid', '--template-id',
                        help='''The template ID of the model to be run.''')
    parser.add_argument('-scids', '--scenario-ids',
                        help='''The scenario IDs of the scenarios to be run,
                        specified as a string containing a comma-separated list of
                        integers. If no IDs are specified, all scenarios associated
                        with the network/template will be run.
                        ''')
    parser.add_argument('-ti', '--initial-timestep',
                        help='''The first timestep of the model.''')
    parser.add_argument('-tf', '--final-timestep',
                        help='''The final timestep of the model.''')
    parser.add_argument('-tsf', '--timestep-format',
                        help='''The format of the timestep (e.g., as found on http://strftime.org).''')
    parser.add_argument('-htsf', '--hydra-timestep-format',
                        help='''The format of a time step in Hydra Platform (found in hydra.ini).''')
    parser.add_argument('-ldir', '--log-dir',
                        help='''The main log file directory.''')
    parser.add_argument('-sol', '--solver',
                        help='''The solver to use (e.g., glpk, gurobi, etc.).''')
    parser.add_argument('-fs', '--foresight',
                        help='''Foresight: 'perfect' or 'imperfect' ''')
    return parser
    
if __name__=='__main__':
    
    parser = commandline_parser()
    args = parser.parse_args()
    
    here = os.path.abspath(os.path.dirname(__file__))
    
    # log file location - based on user
    
    # specify local top-level log dir
    if args.log_dir is None:
        args.log_dir = ''
    args.log_dir = join(here, 'logs', args.log_dir)

    # specify scenarios log dir
    args.scenario_log_dir = 'scenario_logs'
    args.scenario_log_dir = join(args.log_dir, args.scenario_log_dir)

    # make the log dirs - log names should be unique
    if os.path.exists(args.log_dir):
        shutil.rmtree(args.log_dir)
    os.makedirs(args.scenario_log_dir)
    
    # create top-level log file
    logfile = join(args.log_dir, 'log.txt')
    log = create_logger(args.app_name, logfile, '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
    # pre-processing
    for arg in ['network_id', 'scenario_ids', 'template_id']:
        if eval('args.%s' % arg) is not None:
            exec('args.%s = eval(args.%s)' % (arg, arg))
    
    log.info('started model run with args: %s' % str(args))
    
    run_scenarios(args, log)