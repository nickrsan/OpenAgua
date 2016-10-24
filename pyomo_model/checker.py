import os
import argparse
from json import dumps

from utils import create_logger

#import wingdbstub

def get_completed(main_log_dir, scen_log_dir):
    completed = 0
    count = 0
    
    main_log = None
    main_log_path = os.path.join(main_log_dir, 'log.txt')
    if os.path.exists(main_log_path):
        with open(main_log_path, 'r') as f:
            main_log = f.read()
    
    if main_log is None:
        main_log = 'Main log not created yet.'
    
    scen_log = None
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
        
        logfiles = [lf for lf in os.listdir(scen_log_dir) if 'details' in lf]
        if logfiles:
            lfpath = os.path.join(scen_log_dir, logfiles[0]) # UPDATE FOR DIFFERENT SCENARIOS!!!
            with open(lfpath, 'r') as f:
                scen_log = f.read()

    if scen_log is None:
        scen_log = 'Scenario log not created yet.'
        
    result = dumps({'completed': completed,
                    'count': count,
                    'main_log': main_log,
                    'scen_log': scen_log})
    
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
    
    main_log_dir = os.path.join(here, 'logs', args.log_dir)
    scen_log_dir = os.path.join(main_log_dir, 'scenario_logs')
    
    completed = get_completed(main_log_dir, scen_log_dir)