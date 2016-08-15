# The purpose of this script is to calculate
# mean historical monthly runoff for specific
# headflows

import csv, os, sys, pandas as pd, datetime as dt, numpy as np
from os.path import join
from collections import OrderedDict

def datefmt(date):
    return date.strftime('%Y-%m-%d')

def isleapday(d):
    return (d.month==2 and d.day==29)

def parse(row, tolist=None):
    row = row.split("#")[0].strip()
    try:
        vals = eval(row)
    except:
        if ',' in row:
            vals = []
            for s in row.split(','):
                try:
                    vals.append(eval(s))
                except:
                    vals.append(s)
        else:
            vals = row
    if (tolist or type(vals)==tuple) and type(vals)!=list:
        if type(vals)==tuple:
            vals = list(vals)
        else:
            vals = [vals]
    return vals

def get_curr_path():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    return dname

def reset_cwd():
    dname = get_curr_path()
    os.chdir(dname)
    
def set_globals():
    # set up constants
    global mcm2taf, cfs2cms
    mcm2taf = 1/1.2335
    cfs2cms = 1/35.315


def to_dict(df):
    od = OrderedDict()
    for row in df.iteritems():
        od[row[0]] = round(row[1], 3)
    return od 

def get_result(instance, ID, v):
    val = eval('instance.{v}[ID].value'.format(v=v))
    if val==None:
        val = 0.0
    val = round(val, 3)
    return val
        
###def put_prep(outdir, items, scenario):
    
    ###tpl_open = \
###'''
###file {v}_out /..\output\output_{v}.csv/ ;
###{v}_out.pc = 5 ;
###'''
    
    ###tpl_prep = \
###'''
###{v}_out.ap = 0 ;
###put {v}_out ;
###put "{desc}" / ;
###put {scen_cols}, "date", "value" ;
###put / ;
###'''
    
    ###tpl_write = \
###'''
###{v}_out.ap = 1 ;
###put {v}_out ;
###loop((t)$t0(t), put {scen_info} t.tl {v}.l(t):10:3 / ; ) ;
###'''
    ###tpl_close = 'putclose {v}_out;\n'
    
    ###variables = items.keys()
    
    ###scencols = ', '.join(['"{}"'.format(s) for s in scenario.keys()])
    ###sceninfo = ', '.join(['"{}"'.format(s) for s in scenario.values()])
    
    ###with open(os.path.join(outdir, 'put_open.inc'), 'w') as f:
        ###for var in variables:
            ###f.write(tpl_open.format(v=var))
            
    ###with open(os.path.join(outdir, 'put_prep.inc'), 'w') as f:
        ###for var in variables:
            ###f.write(tpl_prep.format(v=var, desc=items[var][0], scen_cols=scencols))    
            
    ###with open(os.path.join(outdir, 'put_write.inc'), 'w') as f:   
        ###for var in variables:
            ###f.write(tpl_write.format(v=var, scen_info=sceninfo))

    ###with open(os.path.join(outdir, 'put_close.inc'), 'w') as f:
        ###for var in variables:
            ###f.write(tpl_close.format(v=var))

def get_price_day(price_year, day):
    price_year = 2006
    try:
        day_price = day.replace(year=price_year)
    except:
        day_price = dt.date(price_year, 3, 1)
    return day_price

# note: this should definitely be a delta, not a dayf, to account for leap years
def get_prices_subset(price_df_all, price_year, day0_price, delta):

    dayf_price = day0_price + delta

    if dayf_price.year == price_year:
        price_t_df = price_df_all.ix[day0_price:dayf_price]
    else:
        price_t_df = pd.concat([\
            price_df_all.ix[day0_price:dt.date(price_year, 12, 31)],
            price_df_all.ix[dt.date(price_year, 1, 1):dt.date(price_year,dayf_price.month,dayf_price.day)]])
        
    return price_t_df
    
    
if __name__=="__main__":
    print('these are functions')
    