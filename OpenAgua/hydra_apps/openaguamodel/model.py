# run the the main scenario-specific routine
# params holds all constant settings
# scenario simply specifies which Hydra scenario to run
def run_scenario(scenario, args=None):
    
    logfile = join(args.scenario_log_dir, 'scenario_{}.log'.format(scenario))
    log = create_logger(args.app_name, logfile)
    log.info('starting scenario {}'.format(scenario))
    
    # log in to Hydra Platform
    log.info('connecting to Hydra Server URL: {}'.format(args.hydra_url))
    conn = connection(url=args.hydra_url, app_name=args.app_name)
    log.info('connected to Hydra Server URL: {}'.format(args.hydra_url))
    try:
        if args.session_id is not None:
            conn.session_id=args.session_id
            log.info('logged in to Hydra Server with provided session ID: %s' % conn.session_id)
        else:
            log.info('attempting to log in...'.format(args.hydra_url))
            conn.login(username='root', password='')
            log.info('logged in to Hydra Server with new session ID: %s' % conn.session_id)
    except:
        log.info('could not log in to Hydra Server')
        raise Exception

    # specify scenario-level parameters parameters (this are sent via params)
    try:
        log.info('creating timesteps')
        ti = dt.datetime.strptime(args.initial_timestep, args.timestep_format)
        tf = dt.datetime.strptime(args.final_timestep, args.timestep_format)
        dates = [date for date in rrule.rrule(rrule.MONTHLY, dtstart=ti, until=tf)]
    except:
        log.info('failed to create timesteps with args: {}'.format(args))
    finally:
        log.info('failed to create timesteps')    
    log.info('running scenario {} for {} months: {} to {}'
             .format(scenario, len(dates), args.initial_timestep, args.final_timestep))

    # create the optimization solver
    solver = SolverFactory(args.solver)      
    










# ===========================
# start the per timestep loop
# ===========================
   
    T = len(dates)
    for t, date in enumerate(dates):
        
        # main per-timestep modeling routine here
        
        #run_timestep(data)
        sleep(.05)
        
        log.info('completed timestep {} | {}/{}'.format(dt.date.strftime(date, args.timestep_format), t+1, T))
    
    return scenario
