import pandas as pd

from flask import session
from datetime import datetime
from dateutil import rrule
from time import mktime

# s = string
def evaluate(s, flavor = 'javaScript'):

    # ============
    # Create dates
    # ============

    # dates are availabe in the data function below

    di = datetime.strptime(session['ti'], session['date_format'])
    df = datetime.strptime(session['tf'], session['date_format'])
    
    # this assumes monthly values
    dates = list(rrule.rrule(rrule.MONTHLY, dtstart=di, until=df))
    
    N = len(dates)

    # =============
    # Evaluate data
    # =============
    
    # Basically, the evaluated string will go into the middle of a def, which
    # is then called.

    
    # create the string defining the wrapper function
    s = s.rstrip()
    lines = s.split('\n')
    if 'return ' not in lines[-1]:
        lines[-1] = 'return ' + lines[-1]
    fs = 'def f(date):\n    %s' % '\n    '.join(lines)
        
    # execute the string to create the wrapper function
    exec(fs, globals())
    
    # finally, call the wrapper function
    # Future: move date to globals, as we might want to add many more variables
    # than just date. Of course, we'll then have to exec(fs) in each date loop.
    #vals = [f(date) for date in dates]
    
    # convert dates
    if flavor=='javaScript':
        dates = [date.strftime(session['date_format']) for date in dates]
       
    # create final result: a dict of values and dates          
    # r = result
    #result = {'dates': dates, 'values': vals}
    result = [{'date': date, 'value': f(date)} for date in dates]
    
    return result
    
def daterange(ti, tf, date_format_in, date_format_out):
    
    start = datetime.strptime(session['ti'], date_format_in)
    end = datetime.strptime(session['tf'], date_format_in)    
    daterange = pd.date_range(start, end, freq='M').tolist()
    daterange = [d.date().strftime(date_format_out) for d in daterange]
    
    return daterange