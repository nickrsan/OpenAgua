import sys
import traceback
from json import loads
from datetime import datetime

from dateutil import rrule, parser
from flask import session
from cryptography.fernet import Fernet

class d2o(object):
    def __init__(self, dictionary):
        for key in dictionary:
            setattr(self, key, dictionary[key])   
            
            
def date_range(start, end, timestep):
    rrule_timestep = eval('rrule.{}'.format(timestep))
    return list(rrule.rrule(rrule_timestep, dtstart=start, until=end)) 


def get_dates(formatted=True):
    start = datetime.strptime(session['ti'], session['date_format'])
    end = datetime.strptime(session['tf'], session['date_format'])    
    timestep = session['timestep']
    dates = date_range(start, end, timestep)
    
    if formatted:
        dates = [date.strftime(session['date_format']) for date in dates]
    
    return dates            
            

def hydra_timeseries(data):
    timeseries = {}
    for row in data:
        date = datetime.strptime(row['date'], session['date_format']) \
            .strftime(session['hydra_time_format'])
        timeseries[date] = str(row['value'])
    timeseries = {'0':timeseries}
    return timeseries


def openagua_timeseries(valstr, **kwargs):
    for key, val in kwargs.items():
        exec('%s = %s' % (key, val))
    dates = get_dates()
    result = list()
    for date in dates:
        value = eval(valstr)
        if eval("'%s'" % value) is None:
            value = ''
        row = {'date': date, 'value': value}
        result.append(row)
    return result


def eval_scalar(x):
    
    try: # create the function
        x = float(x)
    except ValueError as err: # value error
        err_class = err.__class__.__name__
        detail = err.args[0]
        returncode = -1
        errormsg = "%s is not a number" % x
        result = None
    else:
        result = openagua_timeseries('x', x=x)
        returncode = 1
        errormsg = 'No errors!'
    
    return returncode, errormsg, result

    
def eval_descriptor(s):
    result = openagua_timeseries("''")
    returncode = 1
    errormsg = 'No errors!'
    
    return returncode, errormsg, result
    
def eval_generic(x):
    result = openagua_timeseries('x', x=x)
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
    
    result = openagua_timeseries('tsnew[date]', tsnew=tsnew)
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
        dates = get_dates(formatted=False)
        try:
            result = [{'date': date.strftime(session['date_format']),
                       'value': str(f(date))} \
                      for date in get_dates(formatted=False)] 
        except Exception as err: # other error
            err_class = err.__class__.__name__
            detail = err.args[0]
            cl, exc, tb = sys.exc_info()
            line_number = traceback.extract_tb(tb)[-1][1]
        else:
            exception = False # no exceptions

    if exception:
        returncode = -1
        line_number -= 1
        errormsg = "%s at line %d: %s" % (err_class, line_number, detail)
        result = None
    else:
        returncode = 1
        errormsg = 'No errors!'        
        
    return returncode, errormsg, result

def eval_data(data_type, data, do_eval=False, function=None):
    if data_type == 'timeseries' and function:
        returncode, errormsg, timeseries = eval_function(function)
    else:
        returncode, errormsg, timeseries = eval('eval_{}(data)'.format(data_type))

    if timeseries is None:
        timeseries = openagua_timeseries("''")
        
    if do_eval:
        return returncode, errormsg, timeseries
    else:
        return timeseries
    
def encrypt(text, key):
    f = Fernet(key)
    return f.encrypt(str.encode(text))  
    
def decrypt(ciphertext, key):
    f = Fernet(key)
    return f.decrypt(bytes(ciphertext)).decode()

