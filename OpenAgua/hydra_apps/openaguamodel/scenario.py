from __future__ import division

import wingdbstub
from pyomo.core import *
from pyomo_model import create_model, update_instance

def create_model(data):
    
    # create abstract model
    m = AbstractModel()
    
    #
    # sets
    #
    
    # temporal sets
    m.t = Set(initialize=data.t, ordered=True)
    
    # spatial sets (nodes and arcs)
    
    
    # piecewise linear sets
    
    #
    # parameters
    #
    
    # costs (penalties in objective function)
    m.cost = Var(m.t, domain=Reals) # cost
    
    # constants
    m.gamma = Param(initialize=9800)
    
    # initial conditions
    m.S0 = Param(initialize=S0, mutable=True)
    
    # boundary conditions
    # inflows
    m.Qin = Param(m.t, initialize=inflow, mutable=True)
    
    #
    # variables
    #

    # high-level objective function variables
    m.cost_dem = Var(m.d, domain=NonNegativeRealsReals) # shortage for specific demand sites
    m.cost_t = Var(m.t, domain=NonNegativeReals) # shortage for specific 
    
    
    # main decision variables
    m.S = Var(m.t, domain=NonNegativeReals)
    
    # reservoir storage variables
    
    # demand variables
    
    # environmental variables
    
    # 
    
    # ==================
    # objective function
    # ==================
    
    def obj_expression(m):
        return summation(m.cost_dem)
    m.OBJ = Objective(sense=maximize, rule=obj_expression)
    

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

    # ===========================
    # load scenario data
    # ===========================
   
    #conn.

    # ===========================
    # create the optimization solver
    # ===========================

    solver = SolverFactory(args.solver)
   
    # ===========================
    # start the per timestep loop
    # ===========================
   
    T = len(dates)
    for t, date in enumerate(dates):
        
        # ===========================
        # prepare the time steps to use in the optimization run
        # ===========================        

        # ===========================
        # prepare the inflow forecast model
        # ===========================

        # For now, forecast based on mean monthly inflow at each catchment node
        # However, this can be changed in the future

        # ===========================
        # run the model
        # ===========================
        
        if new_model:
            model = create_model(data)
            instance = model.create_instance()            
        else:
            instance = update_instance(instance, S0, inflow)
            instance.preprocess()
            
        # solve the model
        results = solver.solve(instance)
        
        # load the results
        instance.solutions.load_from(results)
        
        # set initial conditions for the next time step
        S0 = instance.S[isIDs[0]].value
        if S0 is None:
            S0 = 0.0
            
        # ===========================
        # save results to memory
        # ===========================
        
        
        log.info('completed timestep {} | {}/{}'.format(dt.date.strftime(date, args.timestep_format), t+1, T))
    
    # ===========================
    # save results to Hydra Server
    # ===========================
    
    
    return
