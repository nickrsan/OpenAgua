import os
import argparse
from json import dumps

from utils import create_logger

def get_completed(logsdir):
    timesteps_completed = 0
    timesteps_count = 0
    for lf in os.listdir(logsdir):
        lfpath = os.path.join(logsdir, lf)
        with open(lfpath, 'rb') as f:
            lastline = f.readlines()[-1]
        parts = lastline.split('|')
        if len(parts) > 1:
            completed, count = parts[-1].split('/')
            timesteps_completed += int(completed)
            timesteps_count = int(count)
            
    result = dumps({'timesteps_completed': timesteps_completed,
                    'timesteps_count': timesteps_count})
    print(result)

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

    parser.add_argument('-dir', '--log-dir',
                        help='''Location of the log files to check.''')
    
    return parser
    
if __name__=='__main__':
    
    parser = commandline_parser()
    args = parser.parse_args()
    
    here = os.path.abspath(os.path.dirname(__file__))
    
    log_dir = os.path.join(here, args.log_dir)
    
    completed = get_completed(log_dir)