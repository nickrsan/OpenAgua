from model import *
from functions_general import *
from functions_price_curves import *
from functions_hydrology import *
# from functions_db import *
import pyomo.environ
from pyomo.opt import SolverFactory
import datetime as dt
from dateutil.relativedelta import relativedelta
from datetime import timedelta as tdelta


def run_scenario(s, p, h, prices_all):

    # create the optimization solver
    solver = SolverFactory(p.solver)      
    
    # start_time = dt.datetime.now()
    
    oneday = dt.timedelta(days=1)
    
    # set up the time step scheme (keep this within this loop--can theoretically be modified under difference scenarios)
    ts_scheme_basic = [1]*s.n_daily+p.ts_scheme_multiday

    # ==========
    # time steps
    # ==========
    
    # run the model d0 to df
    y0 = yf = s.year
    if p.m0 > p.mf:
        y0 -= 1
    date0 = dt.date(y0, p.m0, p.d0)  
    datef = dt.date(yf, p.mf, p.df)  

    days_to_run = pd.date_range(start=date0, end=datef)
    days_to_run = [d.date() for d in days_to_run]
    comp_days = len(days_to_run) - p.days_less

    # days_remaining = min(comp_days, p.days_max)
    days_remaining = comp_days

    # set up the initial ts_scheme
    ts_scheme = ts_scheme_basic[:]
    
    while sum(ts_scheme) < days_remaining:
        ts_scheme.extend([ts_scheme[-1]])      
    
    # cnt_tot = comp_days
    
    # ==================
    # initial conditions
    # ==================
    
    # initial reservior storage
    s_min = min(s.S_max, p.S_min)
    #s0 = min(h['S_sim'].ix[date0], s.S_max)
    S0 = 0.0 # assume reservoir is empty
    new_model = True
    
    # actual SWE
    swe_actual_all = h['SWE_actual_all']
    
    #initial SWE (assume initial SWE is the same as first day; this is strictly not true, but close enough)
    swe_actual_old = swe_actual_all.ix[days_to_run[0]]    
    
    # actual inflows
    infl_actual_all = h['inflow_actual_all']
    
    # initial random error
    err_rand = 0.0
    
    # =====================
    # regression parameters (NB: this probably shouldn't be used until it can be improved)
    # =====================
    '''
    update 11/13/14: the scaling method should be okay
    Also: the regression should be 1) as efficient as possible and 2) re-done for each unique period-of-record
    '''
    new_regression = False
    new_median = False
    # if p.infl_method=='regression':
    #     if new_regression:
    #         regression_params = snow_runoff_regression(swe_actual_all, infl_actual_all,
    #                                                    p.years_of_record, p.infl_method)
    #         regression_params.to_csv('regression_params.csv')
    #     else:
    #         regression_params = pd.read_csv('regression_params.csv', index_col=0)
            
    if p.infl_method=='scaling':
        
        if new_regression:
            # create the regression and write to file
            regression_params = snow_runoff_regression2(swe_actual_all, infl_actual_all, p.years_of_record)
            regression_params.to_csv('inflow_regression_params.csv')
            
        if new_median:
            # get the median hydrograph and write to file
            infl_median = get_infl_median(infl_actual_all)
            infl_median.to_csv('inflow_daily_median.csv', index_col=0)
            
        regression_params = pd.DataFrame.from_csv('inflow_regression_params.csv', index_col=[0,1], header=0)
        infl_median = pd.Series.from_csv('inflow_daily_median.csv', index_col=[0,1], header=0)

    # =============== 
    # main daily loop
    # ===============
    
    idx = [list(s.values) + [today.strftime(p.datefmt)] for today in days_to_run]
    results = []
    infl_all_df = None
    last_day = days_to_run[-1]
    # last_day_tuple = (last_day.month, last_day.day)
    # all_days = [(day.month, day.day) for day in days_to_run]
        
    for d, today in enumerate(days_to_run):

        # (m1,d1) = first_day_tuple = (today.month, today.day)
        (m1,d1) = (today.month, today.day)
        
        if p.profile and d >= 10:
            break
        
        if p.test and d > 2:
            break
        
        # stop running if less than days_less remaining (to ensure last days_max results are omitted from results)
        if days_remaining < p.days_less:
            break
        
        # =================
        # set up time steps
        # =================                  
        
        # shorten the time step scheme and decide if we need to set up a new model
        if d:
            new_model = False  # assume
        if days_remaining > s.n_daily:
            while sum(ts_scheme) > days_remaining:
                ts_scheme[-1] -= 1              
            if ts_scheme[-1] < 0.5*ts_scheme[-2]:
                ts_scheme[-2] += ts_scheme[-1]
                ts_scheme.pop(-1)
                new_model = True
        else:
            ts_scheme.pop(-1)
            new_model = True
            
        days_remaining -= 1       

        # =====================
        # daily time step tasks
        # =====================

        n_daily = ts_scheme.count(1)
        day0 = today
        dayf = day0 + tdelta(n_daily-1)
        tsIDs = range(n_daily)
        tslens = {tsID: 1 for tsID in tsIDs}
        
        # ---------------------
        # hydrologic estimation
        # ---------------------
       
        '''
        This is the heart of this approach, and involves two steps, but only for multiday periods, as n_perfect days are assumed
        to have perfect streamflow foresight (can set n_perfect=1...), and only once at the beginning.
        
        1. On pre-defined dates (update_days), update the snowpack information.
        To mimic our lack of perfect information, we assume that are within a certain range of the assumed actual
        snowpack, i.e. +/- epsilon away from the actual. On average, this means that we get the actual snowpack
        correct. Therefore, we might want to introduce an arbitrary random bias higher or lower than the actual.
        
        2. Use this assumption about snowpack to predict what the inflows are going to be fore the remainder of
        the year, and plan our operations accordingly. This prediction could be based on a range of approaches.
        Two possibilities considered here include a simpe exponential decay function: Q(t)=Q(0)*e^(-k(t-t0)),
        modified slightly. Another possibility is to use some kind of ensemble forecasting, based on runoff under
        conditions previously encountered. For example, average rest-of-year runoff under current (assumed) snowpack
        conditions.
        
        For now, this uses the ensemble forecasting; see get_recession_ensemble for logic.
        
        We might also consider including some kind of hedging in the optimization model, i.e. to account for the
        fact that the prediction is not correct.
        
        '''
                        
        # for now, update on the first day or the first day of every month
        check_snowpack = False
        if s.freq=='monthly':
            if d==0 or today.day==1:
                check_snowpack = True
                # prev_meas_day = today - relativedelta(months=1)
        elif d%p.freq[s.freq]==0:
            check_snowpack = True
            # prev_meas_day = today - relativedelta(days=int(s.freq))
        
        if d==0:
            prev_meas_day = today
            first_meas_day = prev_meas_day            
                
        if check_snowpack:
            
            # actual snowpack
            swe_actual = swe_actual_all.loc[today]

            # =====================
            # SWE measurement model
            # =====================

            # 1. sensor network capability
            alpha_sn = s.alpha_sn
            
            # 2. systematic error
            #eps_sys = s.eps_sys.loc[(m1, d1)]
            swe_err_sys = s.swe_err_sys
            
            # 3. random error
            
            # 3a. mean
            #mu = err_rand # * s.k.loc[(m1, d1)]
            
            # 3b. st. dev.
            
            # calculate cumulative absolute delta swe
            #delta_swe_all = swe_actual_all.ix[date0+oneday:today].values \
                #- swe_actual_all.ix[date0:today-oneday].values
            #delta_swe_all_cum = sum(abs(delta_swe_all))
            
            #delta_swe = swe_actual_all.ix[prev_meas_day+oneday:today].values \
                #- swe_actual_all.ix[prev_meas_day:today-oneday].values
            #delta_swe_cum = sum(abs(delta_swe))
            
            #if delta_swe_all_cum==0:
                #rel_delta_swe_cum = 0.0
            #else:
                #rel_delta_swe_cum = delta_swe_cum / delta_swe_all_cum
            
            ## calculate sigma
            #sigma = rel_delta_swe_cum
                
            
            # 3c. calculate nonsystematic error
            #err_rand = random.gauss(mu, sigma)
            err_rand = 0.0
            
            # 4. calculate modeled SWE measurement error
            #swe_err = (1 + (1 - alpha_sn) * (swe_err_sys + err_rand))
            swe_err = 1 + swe_err_sys
            swe_meas = swe_actual * swe_err

            # =======================
            # inflow prediction model
            # =======================

            # ensemble method (doesn't work well)
            if p.infl_method=='ensemble':
                
                # estimate rest-of-year flow from historical record
                infl_forecast = get_future_ensemble(swe_meas, swe_actual_all, infl_actual_all, today, days_to_run[-1], p.years_of_record) 
                
            # regression method (doesn't work well)
            elif p.infl_method=='regression':
                infl_forecast = pd.Series()
                if (m1, d1)==(2, 29):
                    d1 = 28
                for d in days_to_run:
                    (m2, d2) = (d.month, d.day)
                    if (m2, d2)==(2, 29):
                        d2 = 28
                    #expr = "'(m1=={m1}) & (d1=={d1}) & (m2=={m2}) & (d2=={d2})'".format(m1=m1, d1=d1, m2=m2, d2=d2)
                    #c1, c2 = regression_params.query(expr).values
                    key = '{}-{}-{}-{}'.format(m1, d1, m2, d2)
                    c1, c2 = regression_params.loc[key]
                    Q = max(c1*swe_actual + c2, 0.0)
                    infl_forecast.loc[d] = Q
                    
            elif p.infl_method=='scaling': # seems to work better than the others
                
                # get the rest-of-year median inflow
                dates_remaining = pd.date_range(start=today, end=last_day)
                median_idx = [(day.month, day.day) for day in dates_remaining]
                runoff_median = infl_median.loc[median_idx]
                # if not isleap(today.year) and (2,29) in runoff_median.index:
                #     runoff_median.drop((2,29), inplace=True)
                #
                # get the rest-of-year median inflow sum (total runoff)
                median_runoff_sum = runoff_median.sum()
                
                # Use median flows without modification before Feb.
                if today.month >= 10 or today.month <= 1:
                    infl_forecast = runoff_median
                
                # Scale median flows from Feb. through July.
                elif 2 <= today.month <= 7:
                    # calculate the regressed runoff
                    if (m1,d1)==(2,29):
                        regression_day = (m1,d1-1)
                    else:
                        regression_day = (m1,d1)
                    slope, intercept = regression_params.ix[regression_day][['slope','intercept']]
                    regressed_runoff_sum = swe_meas*slope + intercept
                    
                    # scale the rest-of-year median runoff
                    # THIS NEEDS DOUBLE CHECKING!!!
                    scaling_factor = regressed_runoff_sum / median_runoff_sum
                    infl_forecast = runoff_median * scaling_factor
                    
                # Use actual flows beginning Aug. 1.
                else:
                    infl_forecast = infl_actual_all.loc[today:last_day]
                
                infl_forecast.index = pd.date_range(today, last_day)
                   
        # blend near-term forecast with long-term forecast
        infl_actual = infl_actual_all.loc[day0:last_day]
        infl_forecast = infl_forecast.loc[day0:last_day]
        
        # define alpha (see equation in paper)
        if 8 <= m1 <= 9:
            alpha = p.alpha_initial
        else:
            #blending_start = day0 + relativedelta(days=p.t_blend_start-1)            
            blending_start = day0 + relativedelta(days=s.n_perfect-1)
            blending_end = blending_start + relativedelta(days=s.n_blended-1)

            alpha = pd.Series(index=pd.date_range(start=day0, end=max(blending_end, last_day)))
            alpha.loc[day0:blending_start] = p.alpha_initial
            alpha.loc[blending_end:] = s.alpha_final              
            
            blending_factor = np.linspace(p.alpha_initial, s.alpha_final, num=s.n_blended)
            alpha.loc[blending_start:blending_end] = blending_factor
            alpha = alpha.loc[day0:last_day]
        
        # blend the actual and forecasted inflow
        infl_assumed = alpha*infl_actual + (1-alpha)*infl_forecast
        
        # inflow for the next n_daily days
        inflow = infl_assumed.loc[day0:dayf]
        inflow.index = tsIDs
        inflow = inflow.to_dict()           
        
        # hourly prices for each single day
        day0_price = get_price_day(p.price_year, day0)

        price_day_delta = dayf - day0

        price_daily_df = get_prices_subset(prices_all, p.price_year, day0_price, price_day_delta)
        price_daily_df.index = tsIDs
        prices = to_dict(price_daily_df.stack())
        
        tsIDs_d = tsIDs[:]
        
        # write inflows to database, if debugging
        if p.report_hydrology:

            l = len(infl_assumed)
            infl_df_idx = pd.MultiIndex.from_tuples([tuple(idx[d])], names=p.idx_cols[:])
            stats = pd.DataFrame(index=infl_df_idx)
            o = infl_actual.values
            m = infl_assumed.values
            e = o - m
            o_mean = o.mean()
            m_mean = m.mean()
            e_mean = e.mean()

            # Nash-Sutcliffe model efficiency
            SST = ((o - m)**2).sum()
            SSReg = ((o - o_mean)**2).sum()
            stats['NSE'] = 1 - SST / SSReg
        
            stats['PBIAS'] = pbias = (m - o).sum() / o.sum() * 100
        
            # Mean absolute bias
            stats['ABIAS'] = (abs((m - o) / o)).mean() * 100

            # Price-weighted mean percent bias
            price_today = get_prices_subset(prices_all, p.price_year, day0_price, dt.timedelta(days=0))
            total_price_today = price_today.sum(axis=1)[0]
            price_remainder = get_prices_subset(prices_all, p.price_year, day0_price, price_day_delta)
            total_price_remainder = price_remainder.sum(axis=1).sum()
            mean_price_remaining = total_price_remainder / price_day_delta.days
            price_weight = total_price_today / mean_price_remaining
            stats['PWEIGHT'] = price_weight
            stats['WBIAS'] = price_weight * pbias

            if infl_all_df is None:
                infl_all_df = stats
            else:
                infl_all_df = infl_all_df.append(stats)
        
        # ===============
        # universal tasks
        # ===============        
        
        # prepare revenue curve data frames (these will be empty if multiday==False, but still needed)
        rcurve_ranges_df = pd.DataFrame(columns = p.pieces) # revenue curve ranges
        rcurve_slopes_df = pd.DataFrame(columns = p.pieces) # revenue curve slopes        
        
        # ========================
        # multiday time step tasks
        # ========================                
        
        ts_scheme_md = ts_scheme[n_daily:]
        tsIDs_md = []
        
        if len(ts_scheme_md):
            
            for tslen in ts_scheme_md:
                
                # define initial day0
                day0 = dayf + oneday
                dayf = day0 + tdelta(tslen-1)
                day0_price = get_price_day(p.price_year, day0)
                price_day_delta = dayf - day0

                tsID = tsIDs[-1] + 1
                tsIDs.append(tsID)
                tsIDs_md.append(tsID)
                
                tslens[tsID] = tslen
                
                #
                # estimate inflow from assumed daily inflow (previously calculated)
                #
                            
                inflow[tsID] = infl_assumed.loc[day0:dayf].sum()
                
                # if debug:
                #     inflow_actual_debug[tsID] = inflow_actual.loc[day0:dayf].sum()
                
                #
                # estimate price curves
                #

                price_t_df = get_prices_subset(prices_all, p.price_year, day0_price, price_day_delta)
                
                rcurve_ranges, rcurve_slopes = create_revenue_curve2(prices_df=price_t_df, method=p.rcurve_method, npieces=p.npieces, interval=p.bp_interval)
                #rcurve_ranges, rcurve_slopes = create_revenue_curve(prices_df=price_t_df, npieces=p.npieces)
                
                rcurve_ranges_df.loc[tsID,p.pieces] = rcurve_ranges
                rcurve_slopes_df.loc[tsID,p.pieces] = rcurve_slopes
                          
                
        #if p.test and d==0:
            #rcurve_ranges_df.to_csv('revenue_curve_ranges.csv')
            #rcurve_slopes_df.to_csv('data/revenue_curve_slopes.csv')
            #with open('tslens.csv','w') as f:
                #f.write('TSID,length\n')
                #for k in tslens:
                    #f.write('{},{}\n'.format(k,tslens[k]))
            
        # =======================
        # prepare the whole model
        # =======================
        
        # IDs (time steps)
        ts = {}
        ts['t'] = tsIDs            # all the time steps
        ts['d'] = tsIDs_d   # all the day time steps
        ts['md'] = tsIDs_md  # all the multiday time steps 
            
        # convert revenue curves to dictionary
        rcurve_ranges = rcurve_ranges_df.stack().to_dict()
        rcurve_slopes = rcurve_slopes_df.stack().to_dict()
        
        # ========================
        # create and run the model
        # ========================
        
        if p.run_optimization:
        
            # create model and save it to an instance
            if new_model:
                
                model = create_model(S0, s.Qph_max, s.S_max, s_min, s.IFR, ts, tslens, p.pieces,
                                         inflow, prices, rcurve_ranges, rcurve_slopes)
                
                # create model instance
                instance = model.create_instance()
    
            else:
                instance = update_instance(instance, S0, inflow, prices, tslens, rcurve_ranges, rcurve_slopes)
                
                # preprocess instance
                instance.preprocess()
            
            # optimize
            model_results = solver.solve(instance)
            
            # load model results
            instance.solutions.load_from(model_results)
            
            # =========================
            # update initial conditions
            # =========================
            
            # initial reservoir storage
            S0 = instance.S[tsIDs[0]].value
            if S0==None:
                S0=0.0
            
            # ============
            # save results
            # ============
                
            # output detailed results
            if p.debug:
                #print('[debug] year=%s; day=%s' % (y0, d))
                avg_list = ['Qin_assumed','Qin','Qph','Qll','Qsp','pi','Qifr_min_deficit']
                date2 = today
                for i, ID in enumerate(tsIDs):
                    tslen = ts_scheme[i]
                    date1 = date2
                    date2 = today + dt.timedelta(days=(sum(ts_scheme[:i]) + tslen / 2))
                    date2_str = date2.strftime(p.datefmt)
                    results_today = []
                    
                    for v in p.results_vars:
                        
                        if v=='Qin_actual':
                            val = infl_actual.loc[date1:date2].sum()
                        elif v=='Qin_forecast':
                            val = infl_forecast.loc[date1:date2].sum()
                        elif v=='Qin_assumed' or v=='Qin':
                            val = infl_assumed.loc[date1:date2].sum()
                        else:
                            val = get_result(instance, ID, v)
                            if v=='pi':
                                val /= 1e3 # convert to $k
                        if v in avg_list:
                            val /= float(tslen)
                        results_today.append(val)
     
                    row = idx[d] + [date2_str, tslen] + results_today
                    results.append(row)
                        
            # output basic results     
            else:
                row = idx[d]
                for v in p.results_vars:
                    if v=='Qin_actual':
                        val = infl_actual.mean()
                    elif v=='Qin_forecast':
                        val = infl_forecast.mean()
                    elif v=='Qin_assumed':
                        val = infl_assumed.mean()
                    elif v=='Qin':
                        val = infl_assumed.loc[today]
                    else:
                        val = get_result(instance, tsIDs[0], v)
                        if v=='pi':
                            val /= 1e3 # convert to $k
                    row.append(val)
                results.append(row)   
    
    if p.run_models and p.aggregate:
        col_names = p.idx_cols + p.results_vars
        df = pd.DataFrame(data=results)
        df.set_index(range(len(p.idx_cols)), drop=True, inplace=True)
        df.index.names = p.idx_cols
        grouped = df.groupby(level=p.idx_cols)
        
        # IMPORTANT:
        # this calculates mean daily values, not mean annual values
        agg = grouped.mean()

        agg.columns = p.results_vars
        results = [list(idx)+[round(x,3) for x in row.values] for idx, row in agg.iterrows()]

    if not p.run_optimization:
        results = None

    return results, infl_all_df
