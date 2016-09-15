import argparse
import os
from os.path import join
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
    
    # get connection
    conn = connection(url=args.hydra_url, session_id=args.session_id, log=log)    
    
    # move the following to a function later
    
    # pyomo optimization model
    m = AbstractModel()

    # add nodes and links (arcs)
    network = conn.get_network(args)
    
    m.Nodes = Set(initialize=[n.id for n in network.nodes])
    m.Nodes1 = Set(initialize=[link.node_1_id for link in network.links]) 
    m.Nodes2 = Set(initialize=[link.node_2_id for link in network.links]) 
    m.Links = m.Nodes1 * m.Nodes2
    
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
    
    p = partial(run_scenario, args=args)
    
    log.info('Running {} scenarios in multicore mode with {} workers, {} chunks each.' \
             .format(len(scenarios), poolsize, chunksize))  
    pools = pool.imap(p, scenarios, chunksize=chunksize)
    
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
        """, epilog="For more information visit www.openaguadss.org",
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
    
if __name__=='__main__':
    
    parser = commandline_parser()
    args = parser.parse_args()
    
    here = os.path.abspath(os.path.dirname(__file__))
    
    # specify scenarios log dir
    if args.scenario_log_dir is None:
        args.scenario_log_dir = 'logs'
    args.scenario_log_dir = join(here, args.scenario_log_dir)
    
    # specify local top-level log dir
    if args.log_dir is None:
        args.log_dir = '.'
    args.log_dir = join(here, args.log_dir)

    # top-level log
    logfile = join(args.log_dir, 'log.log')
    log = create_logger(args.app_name, logfile)
    
    log.info('started model run with args: %s' % str(args))
    
    # delete old scenario log files
    for fname in os.listdir(args.scenario_log_dir):
        os.remove(join(args.scenario_log_dir, fname))
    
    run_scenarios(args, log)