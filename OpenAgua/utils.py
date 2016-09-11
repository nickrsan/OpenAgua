import sys
import traceback
from json import loads
from datetime import datetime

from dateutil import rrule, parser
from flask import session

class d2o(object):
    def __init__(self, dictionary):
        for key in dictionary:
            setattr(self, key, dictionary[key])   

def hydra_timeseries(data):
    timeseries = {}
    for row in data:
        date = datetime.strptime(row['date'], session['date_format']) \
            .strftime(session['hydra_time_format'])
        value = row['value']
        timeseries[date] = str(value)
    timeseries = {'0':timeseries}
    return timeseries

def eval_scalar(x):
    dates = get_dates()
    dates = [date.strftime(session['date_format']) for date in dates]
    result = [{'date': date, 'value': x} for date in dates]
    
    returncode = 1
    errormsg = 'No errors!'
    
    return returncode, errormsg, result
    
def eval_generic(x):
    dates = get_dates()
    dates = [date.strftime(session['date_format']) for date in dates]
    result = [{'date': date, 'value': x} for date in dates]
    
    returncode = 1
    errormsg = 'No errors!'
    
    return returncode, errormsg, result
    

def eval_timeseries(timeseries):
    timeseries = loads(timeseries)['0']
    tsnew = dict()
    for item in timeseries.items():
        ts = parser.parse(item[0]).strftime(session['date_format'])
        val = item[1]
        tsnew[ts] = str(val)
    
    dates = get_dates()
    result = list()
    for d in dates:
        date = d.strftime(session['date_format'])
        value = tsnew[d.strftime(session['date_format'])]
        result.append({'date': date, 'value': value})

    returncode = 1
    errormsg = 'No errors!'
    
    return returncode, errormsg, result

def parse_function(s):
    s = s.rstrip()
    lines = s.split('\n')
    if 'return ' not in lines[-1]:
        lines[-1] = 'return ' + lines[-1]
    fs = 'def f(date):\n    %s' % '\n    '.join(lines)
    return fs

# s = string
def eval_function(s):

    # dates
    dates = get_dates()
    
    N = len(dates)

    # create the string defining the wrapper function
    fs = parse_function(s)
    
    # assume there will be an exception:
    exception = True
    
    try: # create the function
        exec(fs, globals())
    except SyntaxError as err: # syntax error
        err_class = err.__class__.__name__
        detail = err.args[0]
        line_number = err.lineno  
    else:
        try:
            result = [{'date': date.strftime(session['date_format']),
                       'value': str(f(date))} for date in dates]   
            exception = False # no exceptions
        except Exception as err: # other error
            err_class = err.__class__.__name__
            detail = err.args[0]
            cl, exc, tb = sys.exc_info()
            line_number = traceback.extract_tb(tb)[-1][1]
            
    if exception:
        returncode = -1
        line_number -= 1
        errormsg = "%s at line %d: %s" % (err_class, line_number, detail)
        result = [{'date': date.strftime(session['date_format']),
                   'value': ''} for date in dates]
    else:
        returncode = 1
        errormsg = 'No errors!'        
        
    return returncode, errormsg, result

def eval_data(data_type, data, do_eval=False, function=None):
    if data_type == 'timeseries' and function:
        returncode, errormsg, timeseries = eval_function(function)
    else:
        returncode, errormsg, timeseries = eval('eval_{}(data)'.format(data_type))
    if do_eval:
        return returncode, errormsg, timeseries
    else:
        return timeseries
    
def date_range(start, end, timestep):
    rrule_timestep = eval('rrule.{}'.format(timestep))
    return list(rrule.rrule(rrule_timestep, dtstart=start, until=end)) 

def get_dates():
    start = datetime.strptime(session['ti'], session['date_format'])
    end = datetime.strptime(session['tf'], session['date_format'])    
    timestep = session['timestep']
    dates = date_range(start, end, timestep)
    
    return dates