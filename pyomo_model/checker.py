import os
import argparse
from json import dumps

from utils import create_logger

#import wingdbstub

def get_completed(scen_log_dir):
    completed = 0
    count = 0
    
    if os.path.exists(scen_log_dir):
        
        logfiles = [lf for lf in os.listdir(scen_log_dir) if 'progress' in lf]
        
        for lf in logfiles:
            lfpath = os.path.join(scen_log_dir, lf)
            with open(lfpath, 'r') as f:
                lines = f.readlines()
                if lines:
                    parts = lines[-1].split('|')
                    if len(parts) > 1:
                        compl, cnt = parts[-1].split('/')
                        completed += int(compl)
                        count = int(cnt)
            
    result = dumps({'completed': completed,
                    'count': count})
    print(result)

def commandline_parser():
    """
        Parse the arguments passed in from the command line.
    """
    parser = argparse.ArgumentParser(
        description="""Check results from the OpenAgua optimization model.
                    Written by David Rheinheimer <david.rheinheimer@itesm.mx>
                    (c) Copyright 2016, Tecnologico de Monterrey.
        """, epilog="For more information visit www.openagua.org",
       formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-ldir', '--log-dir',
                        help='''Location of the log files to check.''')

    return parser
    
if __name__=='__main__':
    
    parser = commandline_parser()
    args = parser.parse_args()
    
    here = os.path.abspath(os.path.dirname(__file__))
    
    scen_log_dir = os.path.join(here, 'logs', args.log_dir, 'scenario_logs')
    
    completed = get_completed(scen_log_dir)