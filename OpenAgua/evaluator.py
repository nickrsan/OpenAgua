# s = string
def evaluate(s, n_years, ts_per_year, ti):

    N = ts_per_year*n_years

    # e = evaluated data
    e = eval(s)
    
    # turn an int into a time series
    # d = data
    if type(e) is int:
        d = [e]*N
    elif type(e) is list:
        if len(e)==ts_per_year:
            d = e*n_years
            
    # l = labels
    l = range(N)
    
    # r = result
    r = {'data': d, 'labels': l}
    
    return r
    
    