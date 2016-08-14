import datetime as dt
import pandas as pd
from collections import OrderedDict
import numpy as np
from functions_general import *
from os.path import join
import itertools

# prepare the scenarios
def prepare_scenarios(v, var_names):
    scenario_vals = [v[c] for c in var_names]
    scenarios = pd.DataFrame(data=list(itertools.product(*scenario_vals)), columns=var_names)
    return scenarios

def cms2mcm(x): return x*0.0864

class params():
    
    project_name = 'SEED'
    shutdown = False
    
    # start and end days within a single water year to run
    m0, d0 = 10, 1
    mf, df = 9, 30
    
    # run switches
    
    profile = False  # output profiling results (doesn't currently work)
    aggregate = True
    debug = False
    test = False
    simple = False
    dbtype = 'sqlite' # options are 'mysql', 'sqlite'
    pooltype = 'imap'  # options are 'imap' and 'map'; the former will update progress
    chunksize = 5  # defines the number of tasks (i.e., years) assigned to each pool worker
    single_db = False # if True, will consolidate results into multiple tables within a single database
    new_db = True # if False, will append to existing db, creating a new one if necessary
    run_models = True # set to false if profiling
    run_optimization = True # set to false if no optimization is to be run (i.e., for reporting hydrology only)
    report_hydrology = False # set to true to output more detailed hydrology
    multicore = True # this is the default
    # if True, will be changed to False under some scenarios
    # set multicore = True to debug full runs
    preprocess_hydrology = False
    postprocess_models = False
    copy_results = False # copy results to another location, such as a dropbox folder
    
    #scenario_sets = ['hydrology']
    #scenario_sets = ['alpha_final', 'alpha_final_matrix', 'IFR', 'n_perfect']
    #scenario_sets = ['SxQph_norm']
    scenario_sets = ['swe_err_sys_matrix']
    #scenario_sets = ['alpha_final']
    
    if simple:
        scenario_sets = ['simple']

    # general
    days_max = 365
    days_less = 0
    rcurve_method = 'intervals' # options are 'intervals' (faster, adaptive) or 'optimized' (probably better)
    infl_method = 'scaling' # options are 'ensemble', 'regression', and 'scaling' (scaling seems to work best)
    npieces = 8
    bp_interval = 25
    solver = 'glpk'  # options are 'glpk' and 'gurobi'
    years_of_record = range(1952, 2009) # can update this as needed
    price_year = 2006
    alpha_initial = 1.0
    
    # directories
    currdir = get_curr_path()
    datadir = join(currdir, 'data')
    indir = join(datadir, '%s/inflow')  
    
    datefmt = '%Y-%m-%d'
    
    # infrastructure
    S_min = 0.0
    
#    # current error characteristics
#    err_sys = 0.0
    
    # climate
    #gcms = miroc5.1
    #rcps = rcp45
    gcms = ['historical']
    rcps = ['maurer.16']
    
    # timesteps
    
    # time period for the whole run (e.g., data availability)
    date_format = '%m/%d/%Y'
    start_date = dt.date(1951, 10, 1)
    end_date = dt.date(2009, 9, 30)
    run_all_years = False
    ts_scheme_multiday = [7, 14]
    start_day = dt.date(2000, m0, d0).strftime('%d-%b')
    end_day = dt.date(2000, mf, df).strftime('%d-%b')
    
    # time span
    tsidx_run = pd.date_range(start=start_date, end=end_date)
    tsidx_run_str = ['{}/{}/{}'.format(d.month, d.day, d.year) for d in tsidx_run]
    
    # piecewise linearization
    if rcurve_method=='intervals':
        breakpoints = breakpoints=range(500,-100,-bp_interval)
        
    # years to run
    if run_all_years:
        v['years'] = list(set([date.year for date in tsidx_run]))
        v['years'] = sorted(years)[1:]
    
    # scenarios - climate
    rcpxgcm = [(rcp,gcm) for rcp in rcps for gcm in gcms]
    projections = ['{}.{}'.format(g, r) for r, g in rcpxgcm]
    
    # load scenario variables
    if rcurve_method=='intervals':
        pieces = ['p{:0>2}'.format(n) for n in range(1,len(breakpoints)+1)]
    else:
        pieces = ['p{:0>2}'.format(n) for n in range(1,npieces+1)]
        
    dtypes = OrderedDict()
    dtypes['alpha_final'] = 'FLOAT'
    dtypes['swe_err_sys'] = 'FLOAT'
    dtypes['n_daily'] = 'INT'
    dtypes['n_perfect'] = 'INT'
    dtypes['n_blended'] = 'INT'
    dtypes['freq'] = 'CHAR(8)'
    dtypes['alpha_sn'] = 'FLOAT'
    dtypes['Qph_max'] = 'FLOAT'
    dtypes['S_max'] = 'FLOAT'
    dtypes['IFR'] = 'FLOAT'
    dtypes['year'] = 'INT'
    dtypes['projection'] = 'CHAR(20)'
    
    scenario_vars = dtypes.keys()
    
    # read in catchment areas
    areas = {}
    areas_f = join(currdir, 'data', 'catchment_area.csv')
    areas_df = pd.read_csv(areas_f, delimiter=',', comment='#', header=True, index_col=0)
    for (c, area) in areas_df.iterrows():
        areas[c] = area.values[0] # area in km^2
    
    # subwats to aggregate
    subwats = ['YUB_{:02}'.format(n) for n in [7,8,10,11,15,16]]
    catchments = [x for x in areas.keys() if x[:6] in subwats]    

    if not aggregate:
        dtypes['date'] = 'DATE'
    if debug:
        dtypes['date2'] = 'DATE'
        dtypes['days'] = 'INT'
    
    #idx_cols = range(len(dtypes))
    idx_cols = dtypes.keys()
    
    results_vars = ['Qin_actual','Qin_forecast','Qin_assumed','Qin',
                    'Qph','Qll','Qsp','S','pi','Qifr_min_deficit']
    
    # freq interval definitions
    freq = {'daily':1, 'weekly':7, 'biweekly':14}
    
    def __init__(self, scenario_set=None):
        
        # variables
        
        v = OrderedDict()

        # set up defaults; scenarios will overwrite these as needed

        v['alpha_final'] = [0.0]
        v['swe_err_sys'] = [0.0]
        v['n_daily'] = [3]
        v['n_perfect'] = [7]
        v['n_blended'] = [8]
        v['freq'] = ['monthly']
        v['alpha_sn'] = [0.0]
        v['Qph_max'] = [cms2mcm(900 / 35.31)] # mcm/day
        v['year'] = range(1952,2010)
        v['S_max'] = [262] # mcm
        v['IFR'] = [cms2mcm(11.0 / 35.31)]
        v['projection'] = [self.projections[0]]

        scenario_class = None

        if scenario_set=='simple':
            v['year'] = [1996]
            v['swe_err_sys'] = [-0.5,0.0,0.5]
            
        elif scenario_set=='hydrology':
            v['alpha_final'] = np.arange(0.0,1.01,0.1)
            v['freq'] = ['monthly','daily']
            
        elif scenario_set=='optimal':
            pass
            
        elif scenario_set=='alpha_sn':
            v['alpha_final'] = [0.0, 1.0]
            v['freq'] = ['monthly', 'daily']
            v['alpha_sn'] = np.arange(0.0, 1.0, 0.2)
        
        elif scenario_set=='n_perfect':
            v['n_perfect'] = np.array([1,7,14,21,365])
            
        elif scenario_set=='alpha_final':
            v['alpha_final'] = np.arange(0.0, 1.01, 0.1)
            v['freq'] = ['monthly','daily']
            
        elif scenario_set=='swe_err_sys_matrix':
            v['swe_err_sys'] = [-0.5,-0.25,0.0,0.25,0.5]
            v['S_max'] = [131., 262.]
            v['freq'] = ['daily', 'monthly']

        elif scenario_set=='alpha_final_matrix':
            v['alpha_final'] = np.arange(0.0, 1.01, 0.1)
            v['S_max'] = [131., 262., 524.]
            v['freq'] = ['monthly', 'daily']    
            
        elif scenario_set=='freq':
            v['alpha_final'] = [0.0, 1.0]
            v['freq'] = ['monthly', 'biweekly', 'weekly', 'daily']
            
        elif scenario_set=='n_perfect':
            v['alpha_final'] = [0.0, 1.0]
            v['n_perfect'] = [7, 14, 21, 28]
            v['alpha_sn'] = [0.0, 1.0]
            
        elif scenario_set=='S_max':
            v['alpha_final'] = [0.0, 1.0]
            v['S_max'] = np.arange(50,450,25) # mcm; actual S_max = 324 mcm
            
        elif scenario_set=='SxQph':
            v['alpha_final'] = [0.0, 1.0]
            v['Qph_max'] = np.arange(0, 2.51, 0.25) # mcm/day
            v['S_max'] = range(0, 601, 50) # mcm; actual S_max = 324 mcm    
        
        #elif scenario_set=='SxQph_norm':
            #v['alpha_final'] = [0.0, 1.0]
            #StoI = np.arange(0, 1.01, 0.1)
            #PtoI = np.arange(0, 2.51, 0.25)
            #v['Qph_max'] = PtoI*1.40392
            #v['S_max'] = StoI*512.4308

        elif scenario_set=='SxQph_norm':
            v['alpha_final'] = [0.0, 1.0]
            StoI = np.arange(0.05, 1.01, 0.1)
            PtoI = np.arange(0.125, 2.51, 0.25)
            v['Qph_max'] = PtoI*1.40392
            v['S_max'] = StoI*512.4308
            
        elif scenario_set=='Qph_max_norm':
            v['alpha_final'] = [0.0, 1.0]
            PtoI = np.arange(0, 6.01, 0.25)
            v['Qph_max'] = PtoI*1.40392
            v['S_max'] = [131,262,524]          
    
        elif scenario_set=='IFR':
            v['alpha_final'] = [0.0, 1.0]
            v['IFR'] = np.arange(0,56,11)/35.31*86400/1e6 # cfs -> mcm/day
        
        self.v = v
        
        if scenario_set != None:
            
            if scenario_class is None:
                if scenario_set is None:
                    scenario_class = 'NA'
                else:
                    scenario_class = scenario_set
            self.scenario_class = scenario_class
            self.scenario_set = scenario_set
            self.scenarios = prepare_scenarios(v, self.scenario_vars) 
            
            db_name = self.project_name
            
            if self.simple:
                run_name = 'simple'
                #self.multicore = False
            else:
                run_name = scenario_set

            if self.single_db==False:
                db_name += '_' + run_name
                
            if self.debug:
                run_name += '_debug'
                db_name += '_debug'
                
            if self.test:
                run_name += '_test'
                db_name += '_test'
                #self.multicore = False   
                
            self.run_name = run_name
            self.db_name = db_name
