from dateutil import rrule, parser

from json import loads
from flask import session
from datetime import datetime
from dateutil import rrule
from time import mktime

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
    return result

def eval_timeseries(timeseries):
    timeseries = loads(timeseries)['0']
    tsnew = dict()
    for item in timeseries.items():
        ts = parser.parse(item[0]).strftime(session['date_format'])
        val = item[1]
        tsnew[ts] = val
    
    dates = get_dates()
    result = list()
    for d in dates:
        date = d.strftime(session['date_format'])
        value = tsnew[d.strftime(session['date_format'])]
        result.append({'date': date, 'value': value})
    return result

# s = string
def eval_descriptor(s, flavor = 'javaScript'):

    # dates
    dates = get_dates()
    
    N = len(dates)

    # create the string defining the wrapper function
    s = s.rstrip()
    lines = s.split('\n')
    if 'return ' not in lines[-1]:
        lines[-1] = 'return ' + lines[-1]
    fs = 'def f(date):\n    %s' % '\n    '.join(lines)
        
    # create the function
    exec(fs, globals())
    
    # create final result          
    result = [{'date': date.strftime(session['date_format']),
               'value': f(date)} for date in dates]
    
    return result  
    
#def daterange(date_format_in, date_format_out):
    #start = datetime.strptime(session['ti'], date_format_in)
    #end = datetime.strptime(session['tf'], date_format_in)    
    #daterange = date_range(start, end, freq='M').tolist()
    #daterange = [d.date().strftime(date_format_out) for d in daterange]
    
    #return daterange

def date_range(start, end, timestep):
    rrule_timestep = eval('rrule.{}'.format(timestep))
    return list(rrule.rrule(rrule_timestep, dtstart=start, until=end)) 

def get_dates():
    start = datetime.strptime(session['ti'], session['date_format'])
    end = datetime.strptime(session['tf'], session['date_format'])    
    timestep = session['timestep']
    dates = date_range(start, end, timestep)
    
    return dates