from functions_general import *
from functions_db import *
from functions_scenario import *
from params import *
from progressbar import ProgressBar, Percentage, Bar, ProgressBar, ETA, Timer
from time import sleep

import itertools
import cProfile
import pstats
import shutil

def main(p, currdir, datadir, indir, results_dir, results_name, new_db):
    
    # =====
    # input
    # =====
    
    # general parameters
    if p.debug:
        results_name += '_debug'
    if p.aggregate and p.dbtype=='csv':
        results_fpath_agg = join(results_dir, (results_name + '_aggregate.csv'))
    dayfmt = '{:4}-{:0>2}-{:0>2}' # unused for now; might want to update the gamsIDs with this
    
    # ===============================
    # initializations & preprocessors
    # ===============================
    reset_cwd()
    
    # create global variables
    set_globals()
    
    results_tbl = results_name
    
    db_path = join(results_dir, '{}.sqlite'.format(p.db_name))
    conn = db_connect(db_path, flavor='sqlite', new_db=new_db)  
    
    # ==============================
    # hydrologic info pre-processing
    # ==============================
    
    hydrodata = {}
   
    # WARNING: The following is old; need to update for multiprocessing!!!
    for proj in p.projections:
        
        # define paths
        climdir = join(datadir, 'hydrology', proj)
        climdir_ops = join(datadir, 'operations', proj)    
        
        swe_path = join(climdir, 'SWE_actual_all.csv') 
        infl_path = join(climdir, 'inflow_actual_all.csv')
        storage_path = join(climdir_ops, 'storage_simulated.csv')
    
        # write to csv
        if p.preprocess_hydrology:

            # SWE
            swe_path_in = join(climdir, 'SnowAccumulation.csv')
            swe_actual_all = get_swe(swe_path_in, params)            
            swe_actual_all.to_csv(swe_path)
            
            # inflow
            infl_path_in = join(climdir, 'Flow to River.csv')
            inflow_actual_all = get_infl(infl_path_in, params)
            inflow_actual_all.to_csv(infl_path)
            
            # reservoir storage
            storage_path_in = join(climdir_ops, 'Reservoir Storage Volume.csv')
            S_sim = get_storage(storage_path_in, params)
            S_sim.to_csv(storage_path)
        
        # read from csv
            
        # SWE
        hydrodata['SWE_actual_all'] = pd.Series.from_csv(swe_path, index_col=0)
        
        # inflow
        hydrodata['inflow_actual_all'] = pd.Series.from_csv(infl_path, index_col=0)
        
        # storage
        hydrodata['S_sim'] = pd.Series.from_csv(storage_path, index_col=0)
    
    # =====================================
    # electricity price info pre-processing
    # =====================================
    
    # get the actual hourly electricity prices
    prices_path_in = join(datadir, 'electricity_prices.csv')
    prices_all = pd.DataFrame.from_csv(prices_path_in, index_col=0, parse_dates=True)                
        
    # ============
    # create model
    # ============

    '''
    The 'model' is just set up here, with limited initialization.
    It is actually constructed (parameterized) below.
    '''
    
    ##model = create_model()  

    # ======================
    # run scenarios
    # ======================
    scenarios = [s for i, s in p.scenarios.iterrows()]

    print('')
    print('SCENARIO PARAMETERS:')
    for v in p.v.keys():
        vals = p.v[v]
        if len(vals) <= 3:
            vals_str = str(vals)
        else:
            vals_str = '[%s, %s, ..., %s] (%s values)' % (vals[0], vals[1], vals[-1], len(vals))
        print('{:<20} {:<15}'.format(v, vals_str))    
    print('')
    print('Number of scenarios: %s' % len(scenarios))
    print('Start time: ' + str(dt.datetime.now()))
    print('')
    print('PROGRESS:')

    results = []

    N = len(scenarios)
    start_time = dt.datetime.now()
    
    def report_progress(n):
        elapsed_time = (dt.datetime.now() - start_time).seconds / 60.
        avg_secs = elapsed_time * 60. / (n+1)
        remaining_secs = (N-(n+1)) * avg_secs
        remaining_hours = int(floor(remaining_secs/3600))
        remaining_minutes = int(floor(remaining_secs/60-remaining_hours*60))
        remaining_seconds = round(remaining_secs - remaining_minutes*60 - remaining_hours*3600,1)
        remaining_str = '{}:{}:{}'.format(remaining_hours,remaining_minutes,remaining_seconds)
        msg = '\r{: 4}/{} ({:.1%}) completed. {:.2f} min. elapsed; {} remaining. ' \
            .format(n+1, N, float(n+1)/N, elapsed_time, remaining_str)
        print(msg),
    
    if p.multicore:
        
        # ==================
        # multi core routine
        # ==================
        
        import multiprocessing as mp
        from functools import partial 
        
        poolsize = mp.cpu_count()
        print('Running in multicore mode with pool.{}: {} workers, {} chunks each.' \
              .format(p.pooltype, poolsize, p.chunksize))
        print('Progress will be reported here.') #% (poolsize*p.chunksize))
        pbar = ProgressBar(widgets=[Timer(), ' ', Percentage(), ' ', Bar(marker='O'),
                                    ' ', ETA()],
                           maxval=len(scenarios)).start()
        
        pool = mp.Pool(processes=poolsize, maxtasksperchild=1)
        
        # set up the partial function
        f = partial(run_scenario, p=p, h=hydrodata, prices_all=prices_all)
        
        if p.pooltype=='map':
            results = pool.map(f, scenarios, chunksize=1)
            
            # store results
            print('writing results')
            for (result, infl_all_df) in enumerate(results):
                if p.dbtype=='csv':
                    results.append(result)
                elif p.dbtype in ['mysql', 'sqlite']:
                    db_insert_many(conn, results_tbl, p.idx_cols + p.results_vars, result[1], p.dtypes)
                    
        elif p.pooltype=='imap':
            pools = pool.imap(f, scenarios, chunksize=p.chunksize)                 
            for n, (result, infl_all_df) in enumerate(pools):
                pbar.update(n)
                        
                if result is not None:
                    db_insert_many(conn, results_tbl, p.idx_cols + p.results_vars, result, p.dtypes)
                    
                if infl_all_df is not None:
                    df_to_sql(conn, infl_all_df, 'Qin_stats', p.dtypes)                 
                     
                #if (n+1)%(p.chunksize*poolsize)==0 or (n+1)==len(scenarios):
                    #report_progress(n)          
        
        # stop the pool
        pool.close()
        pool.join()
        pbar.finish()
                
    else:
        
        # ===================
        # single core routine
        # ===================
        
        for n, scenario in enumerate(scenarios):
            if p.debug:
                print('{}\nScenario started: {} of {}\n{}'.format(dt.datetime.now(), n+1, N, scenario))
            result, infl_all_df = run_scenario(s=scenario, p=p, h=hydrodata, prices_all=prices_all)
            
            if result is not None:
                db_insert_many(conn, results_tbl, p.idx_cols + p.results_vars, result, p.dtypes)
            
            if infl_all_df is not None:
                df_to_sql(conn, infl_all_df, 'Qin_stats', p.dtypes)
                
            report_progress(n)
        
    # close the database           
    conn.commit()
    conn.close()

    print('finished')

if __name__=='__main__':

    p = params(scenario_set=None)
    
    # general parameters
    currdir = get_curr_path()
    datadir = join(currdir, 'data')
    indir = join(datadir, '%s/inflow')
    
    print('')
    print('GENERAL PARAMETERS:')
    for param in ['profile','debug','multicore','test','simple',
                  'rcurve_method', 'infl_method',
                  'solver',
                  'ts_scheme_multiday',
                  'start_day','end_day']:
        print('{:<20} {:<15}'.format(param, str(eval('p.'+param))))    
    
    if p.profile:
        p = params(scenario='simple')
        
        cProfile.run('main(p)', 'profile.txt')
        
        stats = pstats.Stats('profile.txt')
        
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        
        stats.print_stats()
    
    elif p.run_models:
        scenario_sets = p.scenario_sets
        for c, s_set in enumerate(scenario_sets):
            print('')
            print('======NEW SCENARIO SET (%s of %s)========' % (c+1, len(scenario_sets)))
            print('')
            print('Scenario set name: "%s"' % s_set)
            print('')
            print('initializing...')
            
            p = params(scenario_set=s_set)
            
            results_name = 'results_{}'.format(p.scenario_class)
            
            if (c==0 or p.single_db==False) and p.new_db:
                new_db = True
            else:
                new_db = False
            
            # define and create output directory
            if new_db:
                run_suffix = dt.datetime.today().strftime('%Y%m%d')
            else:
                run_suffix = 'current'
            results_dir = join(currdir, 'results_' + run_suffix)
            copy_suffix = '_copy_' + dt.datetime.now().strftime('%m%d%H%M')
            if os.path.exists(results_dir):
                if new_db:
                    shutil.move(results_dir, results_dir + copy_suffix)
                    os.mkdir(results_dir)
                else:
                    shutil.copytree(results_dir, results_dir + copy_suffix)
            else:
                os.mkdir(results_dir)
            if p.copy_results:
                results_dir_share = join('/home/david/Dropbox/PROJECTS/CITRIS/SEED_basic/results_' + p.run_suffix)
                if os.path.exists(results_dir_share):
                    shutil.move(results_dir_share, results_dir_share + copy_suffix)
                os.mkdir(results_dir_share)       
                
            # run model
            main(p, currdir, datadir, indir, results_dir, results_name, new_db)
            
        if p.postprocess_models:
            from SEED_postprocess import *
            for c, s_set in enumerate(scenario_sets):
                print('')
                print('======POSTPROCESSING SCENARIO (%s of %s)========' % (c+1, len(scenario_sets)))
                print('')
                print('Scenario set name: "%s"' % s_set)
                print('')
                print('initializing...')
  
                postprocess(p, db_name, s_set)
            
    
    if p.copy_results:
        print('copying results to dropbox...')
        shutil.copytree(src=results_dir, dst=results_dir_share)
    
    print('\nfinished.')
    
    if p.shutdown:
        os.system('shutdown -h +10')
    
