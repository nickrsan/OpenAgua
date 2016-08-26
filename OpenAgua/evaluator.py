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
    exec(fs)
    
    # finally, call the wrapper function
    # Future: move date to globals, as we might want to add many more variables
    # than just date. Of course, we'll then have to exec(fs) in each date loop.
    vals = [f(date) for date in dates]
    
    # =============
    # convert dates
    # =============

    if flavor=='javaScript':
        dates = [int(mktime(d.timetuple())) * 1000 for d in dates]    
       
    # create final result: a dict of values and dates          
    # r = result
    result = {'dates': dates, 'values': vals}
    
    return result
    
    