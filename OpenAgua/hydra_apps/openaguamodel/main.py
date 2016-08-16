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

# the main per time step routine
def run_timestep(data):
    
    return 5

# run the the main scenario-specific routine
# params holds all constant settings
# scenario simply specifies which Hydra scenario to run
def run_scenario(scenario, args=None):
    
    logfile = join(args.scenario_log_dir, 'scenario_{}_log.txt'.format(scenario))
    log = create_logger(args.app_name, logfile)
    log.info('starting scenario {}'.format(scenario))
    
    # log in to Hydra Platform
    log.info('connecting to Hydra Server URL: {}'.format(args.hydra_url))
    conn = connection(url=args.hydra_url, app_name=args.app_name)
    log.info('connected to Hydra Server URL: {}'.format(args.hydra_url))
    try:
        if args.session_id is not None:
            conn.session_id=args.session_id
            log.info('logged in to Hydra Server with provided session ID: %s' % conn.session_id)
        else:
            log.info('attempting to log in...'.format(args.hydra_url))
            conn.login(username='root', password='')
            log.info('logged in to Hydra Server with new session ID: %s' % conn.session_id)
    except:
        log.info('could not log in to Hydra Server')
        raise Exception

    # specify scenario-level parameters parameters (this are sent via params)
    ti = dt.datetime.strptime(args.initial_timestep, args.timestep_format)
    tf = dt.datetime.strptime(args.final_timestep, args.timestep_format)
    dates = [date for date in rrule.rrule(rrule.MONTHLY, dtstart=ti, until=tf)]
    log.info('running scenario {} for {} months: {} to {}'
             .format(scenario, len(dates), args.initial_timestep, args.final_timestep))
    
    T = len(dates)
    for t, date in enumerate(dates):
        
        # main per-timestep modeling routine here
        
        #run_timestep(data)
        sleep(.5)
        
        log.info('completed timestep {} [{}/{}]'.format(dt.date.strftime(date, args.timestep_format), t+1, T))
    
    return scenario

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

    logfile = join(args.log_dir, 'log.txt')
    log = create_logger(args.app_name, logfile)
        
    log.info('started model run with args: %s' % str(args))
    
    # delete old scenario log files
    
    rmtree(args.scenario_log_dir, ignore_errors=True)
    os.mkdir(args.scenario_log_dir)
    
    run_scenarios(args)