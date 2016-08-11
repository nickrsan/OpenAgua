import datetime as dt
import numpy as np
import pandas as pd
import random
from calendar import isleap
#import matplotlib.pyplot as plt

def jday(day):
    return day.timetuple().tm_yday

def jdays(days):
    for day in days:
        yield jday(day)

# get the actual inflow
def get_actual_inflow(df, day0, dayf):
    inflow_actual = df.ix[day0:dayf].sum()[0]
    return inflow_actual

# get the mean inflow
def get_mean_inflow(df, day0, ndays):
    dayslist = [((day0+dt.timedelta(days=j)).month, (day0+dt.timedelta(days=j)).day) for j in range(ndays)]
    inflow_mean = df.loc[dayslist].sum()[0]
    return inflow_mean

def create_ts_index(fpath):
    # this creates a data frame template with the daily time series days as the index
    tsidx = pd.Series.from_csv(fpath, header=0).index
    return tsidx

# calculate mean monthly headflow
# should update to specify the date range
def get_headflows_mean(df, yi, yf):

    df = df.ix[(yi,10):(yf,9)]
    df = df.groupby(level=1).mean() # no conversion; units are cms
    # NB: level 1 is the second index level, i.e. month
    
    return df

# SnowAccumulation = m; areas = km^2; Dsnow = m
def get_swe(csv_path, params):
    df = pd.read_csv(csv_path, index_col=0, parse_dates=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[params.tsidx_run_str, params.catchments]
    df.index = params.tsidx_run
    total_area = 0.0
    for c in params.catchments:
        df[c] = df[c] * params.areas[c]
        total_area += params.areas[c]
    Vsnow_actual_all = df.sum(axis=1)
    swe_actual_all = Vsnow_actual_all / total_area
    
    return swe_actual_all

# 'Flow to River' is in m^3; convert to mcm
def get_infl(csv_path, params):
    
    df = pd.read_csv(csv_path, index_col=0, parse_dates=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[params.tsidx_run_str, params.catchments]
    df.index = params.tsidx_run
    inflow_actual_all = df.sum(axis=1) / 1e6
    
    return inflow_actual_all

def get_storage(csv_path, params):
    # note: usecols includes Upper Yuba reservoirs to be aggregated
    df = pd.read_csv(csv_path, usecols=[0,1,3,4,5], index_col=0, parse_dates=False)
    df = df.loc[params.tsidx_run_str,:]
    df.index = params.tsidx_run
    S_sim = df.sum(axis=1) / 1e6 # convert to mcm
    
    return S_sim

# converts daily YRS flows to monthly volumes 
def get_YRS_monthly(indir, hfs):
    
    ts = pd.Series(0, index=tsidx)
    
    # loop through the headflows
    for fpath in [os.path.join(indir, hf + '.csv') for hf in hfs]:        
        ts += pd.Series.from_csv(fpath, parse_dates=False, header=1).values
    
    # calculate monthly flows, convert from cms to mcm
    ts = ts.groupby([ts.index.year, ts.index.month]).sum()*3600*24/1e6
            
    return ts

# calculate the historical median monthly flow
def get_YRS_medians(ts, yi, yf):
    
    ts = ts.ix[(yi,10):(yf,9)]
    ts = ts.groupby(level=1).median()
    
    return ts

# calculate the WYI for the current month
# IMPORTANT: triple-check this formula!!!
# note: formulat assumes YRS is in mcm
# unit conversion is at the bottom
def YRS_WYI(YRS, WYI0, y, m):
    
    if m==10:
        WYI = YRS.ix[(y-1,10):(y,9)].sum()*mcm2taf
    elif m>10 or m<2:
        WYI = WYI0
    elif m in [2,3,4,5]:

        # year-to-date
        YTD = YRS[(y-1,10):(y,m-1)].sum()
        
        # forecast (for now, assume perfect foresight; can update this later)
        forecast = YRS[(y,m):(y,9)].sum()
        
        WYI = (YTD + forecast)*mcm2taf
    else:
        WYI = WYI0
    
    return WYI
    
def YRS_WYT(WYI, WYT_defs):
    for WYT in WYT_defs.keys():
        if WYI <= WYT_defs[WYT]:
            break
    return WYT
       
def get_UYR_eflows(IFR_defs, WYT, YRS_medians, ts):

    nodes = IFR_defs.keys()

    y0, m0 = ts[0]
    
    beforefeb = m0 >= 10 or m0 < 2
    
    # initialize
    df = pd.DataFrame(index=ts)
    for node in nodes:

        IFRs = []
        for i, (y,m) in enumerate(ts):
            
            # conservatively assume BN for Feb-Sep if starting month is before Feb
            # UPDATE LATER!!!
            if beforefeb and (m >= 2 and m <= 9) :
                WYT = 'BN'
        
            IFRs.append(IFR_defs[node][(WYT,m)])
            
        df[node] = IFRs
        
    return df
    
def get_future_ensemble(Dsnow_meas, Dsnow_actual_all, inflow_actual_all, day0, dayf, years_of_record):
    
    delta = dayf - day0
    
    snow_dates = []
    ensemble_flows = pd.DataFrame()

    # get the years having Dsnow closest to today
    thisdays = []
    for y in years_of_record:
        try:
            thisday = day0.replace(year=y)
        except:
            thisday = day0.replace(year=y, day=28)  # today is a leapday; use Feb. 28 instead
        thisdays.append(thisday)
        
    Dsnow_today_all = Dsnow_actual_all.loc[thisdays].round(3)  # round to the nearest cm
    Dsnow_diff = np.abs(Dsnow_today_all - Dsnow_meas)
    Dsnow_diff.sort()
    ensemble_years = []
    i = 0
    while i < len(Dsnow_diff) and (Dsnow_diff.iloc[i] <= 0.01 or i < 5): # Dsnow in m, so 0.01 = 1cm (very low)
        ensemble_years.append(Dsnow_diff.index[i].year)
        i += 1
    
    # get total runoff for rest of year
    total_runoff_all = [inflow_actual_all.loc[thisdays[i]:thisdays[i]+delta].sum() for i in range(len(years_of_record))]
            
    # get ensemble flows and volumes
    for y in ensemble_years:
        try:
            thisday = day0.replace(year=y)
        except:
            thisday = day0.replace(year=y, day=28)  # today is a leapday; use Feb. 28 instead
        
        flows = inflow_actual_all.loc[thisday:thisday+delta]
        
        ensemble_flows[y] = flows.values
    
    # use mean daily flow for ensemble
    ensemble_flows.index = pd.date_range(start=day0, end=day0+delta)
    ensemble_flows.index.name = 'Date'
    ensemble_flows.columns.names = ['Flow']
    ensemble_flows = ensemble_flows.mean(axis=1)
    
    # finally, scale the ensemble flow according to a regression between current snow and future runoff magnitude
    # but only do this if there are sufficient non-zero (>= 1mm) snow days
    if len(Dsnow_today_all.unique()) >= 0.75 * len(Dsnow_today_all):
        m, b = np.polyfit(x=Dsnow_today_all, y=total_runoff_all, deg=1)
        total_runoff_today = m * Dsnow_actual_all.loc[day0] + b
        ensemble_runoff_today = ensemble_flows.sum()
        r = total_runoff_today / ensemble_runoff_today
        ensemble_flows = ensemble_flows * r
    
    return ensemble_flows

# This method does not work well. Need to have a more robust predictive model.
def snow_runoff_regression(D, Q, yrs, flavor, makeplots=False):
    from scipy.stats import linregress
    
    days1 = sorted(set([(date.month, date.day) for date in D.index]))
    
    params = []
    idx = []
    
    for day1 in days1:
        
        # create the dates
        m1, d1 = day1
        try:
            Didx = [dt.date(y, m1, d1) for y in yrs]
        except:
            continue
        if (m1, d1) == (9, 16):
            break
        
        # get the depth (SWE) for each date
        depths = D.loc[Didx]
        
        if flavor=='regression':
            days2 = days1[days1.index(day1):]
            for day2 in days2:
                m2, d2 = day2
                try:
                    Qidx = [dt.date(y, m2, d2) for y in yrs]
                except:
                    continue
                Q2 = Q.loc[Qidx]
                
                z = c1, c2 = np.polyfit(x=D1, y=Q2, deg=1)
                c1 = round(c1, 3)
                c2 = round(c2, 3)
                
                idx.append('{}-{}-{}-{}'.format(m1,d1,m2,d2))
                
                params.append((c1, c2))
                
        elif flavor=='scaling':
            
            runoffs = []
            
            for y in yrs:
                #Qidx = [dt.date(y, m2, d2) for (m2, d2) in days2]
                Qidx = pd.date_range(start=dt.date(y, m1, d1), end=dt.date(y, 9, 15))
                Qsum = Q.loc[Qidx].sum()
                runoffs.append(Qsum)
            #z = c1, c2 = np.polyfit(x=depths, y=Q2, deg=1)
            slope, intercept, r_value, p_value, std_err = linregress(x=depths, y=runoffs)
            params.append([slope, intercept, r_value**2])
            
    regression_params = pd.DataFrame(data=params, index=idx, columns=['slope', 'intercept', 'R2'])
    
    return regression_params

# regression between each day and rest-of-year runoff
def snow_runoff_regression2(D, Q, yrs):
    from scipy.stats import linregress
    
    days = sorted(set([(date.month, date.day) for date in D.index]))
    
    params = []
    idx = []
    
    for m, d in days:
        
        # create the dates
        try:
            Didx = [dt.date(y, m, d) for y in yrs]
        except:
            continue
        if m > 8:
            break
        
        # get the depth (SWE) for each date
        depths = D.ix[Didx]
        
        runoffs = []
        
        for y in yrs:
            Qidx = pd.date_range(start=dt.date(y, m, d), end=dt.date(y, 9, 15))
            Qsum = Q.ix[Qidx].sum()
            runoffs.append(Qsum)
        slope, intercept, r_value, p_value, std_err = linregress(x=depths, y=runoffs)
        params.append([slope, intercept, r_value**2])
        idx.append((m,d))
    midx = pd.MultiIndex.from_tuples(idx, names=['month','day'])
    regression_params = pd.DataFrame(data=params, index=midx, columns=['slope', 'intercept', 'R2'])
    
    return regression_params

def get_infl_median(infl_actual_all):
    infl = pd.DataFrame(data = infl_actual_all)
    infl.index = pd.MultiIndex.from_tuples([(d.month, d.day) for d in infl.index])
    infl_median = infl.median(level=[0,1])
    infl_median.index.names = ['month','day']
    infl_median.columns = ['Qin']
    
    return infl_median