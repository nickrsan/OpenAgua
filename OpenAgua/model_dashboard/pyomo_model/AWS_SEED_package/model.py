from __future__ import division
from pyomo.core import *

# This model optimizes a hydropower maximization problem

def create_model(S0, Qph_max, S_max, S_min, IFR, ts, tslens, pieces, inflow,
                 prices, rcurve_ranges, rcurve_slopes):
    
    # create abstract model
    m = AbstractModel()
    
    #
    # sets
    #
    
    # temporal sets
    m.t = Set(initialize=ts['t'], ordered=True)
    m.d = Set(within=m.t, initialize=ts['d'], ordered=True)
    m.md = Set(within=m.t, initialize=ts['md'], ordered=True)
    h = ['H{:0>2}'.format(i) for i in range(1,25)]
    m.h = Set(initialize=h, ordered=True) # all hours of the day
    m.dh = m.d*m.h
    
    # piecewise linear sets
    m.p = Set(initialize=pieces)
    m.mdp = m.md*m.p
    
    #
    # parameters
    #
    
    # constants
    m.gamma = Param(initialize=9800) # specific weight of water (N per m^3)
    
    # constants for now
    m.head = Param(initialize=957)
    m.head_ll = Param(initialize=30) # assume this is the average ll outlet head
    m.S_min = Param(initialize=S_min)
    m.S_max = Param(initialize=S_max)
    #m.dS_low_lim = Param(initialize=1e6)
    #m.dS_high_lim = Param(initialize=1e6)
    m.Qph_max = Param(initialize=Qph_max) # daily powerhouse capacity
    m.Qll_max = Param(initialize=IFR) # daily low level outlet capacity
    m.Qifr_min = Param(initialize=IFR) # daily IFR (mcm/day)
    m.C_ifr_low = Param(initialize=1e6) # cost of min IFR deficit
    m.ESV = Param(initialize=1e3)
    
    # time step lengths
    m.ndays = Param(m.t, initialize=tslens, mutable=True)
    
    # initial conditions
    m.S0 = Param(initialize=S0, mutable=True) # initial reservoir storage
    
    # inflows
    m.Qin = Param(m.t, initialize=inflow, mutable=True)
    
    # electricity prices
    
    # base load
    m.base_load_price = Param(initialize=0.0)
    
    # hourly prices for daily operations
    m.price = Param(m.t, m.h, initialize=prices, mutable=True)
    
    # revenue curves for multiday operations
    m.rc_range = Param(m.t, m.p, initialize=rcurve_ranges, mutable=True)
    m.rc_slope = Param(m.t, m.p, initialize=rcurve_slopes, mutable=True)

    #
    # variables
    #
    
    # high level variables
    m.pi = Var(m.t, domain=Reals) # hydropower revenue during each time step
    m.pi_ll = Var(m.t, domain=Reals) # hydropower revenue from low level outlet powerhouse
    m.C_ifr = Var(m.t, domain=NonNegativeReals) # cost of unmet IFRs    
    m.B_S = Var(m.t, domain=NonNegativeReals) # benefit of storage
    
    # main decision variables
    m.Qin_assumed = Var(m.t, domain=NonNegativeReals) # daily assumed inflow
    m.Qph = Var(m.t, domain=NonNegativeReals) # "daily powerhouse flow"
    m.Qph_piece = Var(m.t, m.p, domain=NonNegativeReals) # "daily powerhouse piecewise flow"
    m.Qph_h = Var(m.dh, domain=NonNegativeReals) # "hourly powerhouse flow"
    m.Qsp = Var(m.t, domain=NonNegativeReals) # "daily spill"
    m.Qll = Var(m.t, domain=NonNegativeReals) # "daily low level outlet"
    m.Qll_h = Var(m.t, m.h, domain=NonNegativeReals) # "hourly low level outlet flow"
    m.S = Var(m.t, domain=NonNegativeReals) #   "daily reservoir storage"

    # reservoir storage variables
    m.dS_low = Var(m.t, domain=NonNegativeReals) # "storage delta above decrease target"
    m.dS_high = Var(m.t, domain=NonNegativeReals) # "storage delta above increase target"
    
    # environmental variables
    m.Qifr_min_deficit_h = Var(m.t, m.h, domain=NonNegativeReals) # "hourly IFR flow deficit"
    m.Qifr_min_deficit = Var(m.t, domain=NonNegativeReals) # "multiday IFR flow deficit"
    
    # other supporting variables
    m.Si = Var(m.t, domain=NonNegativeReals) # initial storage during each time step
    m.S_space = Var(m.t, domain=NonNegativeReals)
    
    # some misc. variables are also included below
    
    #
    # equations
    #
    
    # ==================
    # objective function
    # ==================
    
    def obj_expression(m):
        return summation(m.pi) + summation(m.pi_ll) - summation(m.C_ifr)# + summation(m.B_S)# - 1e6*summation(m.Qsp)
    
    m.OBJ = Objective(sense=maximize, rule=obj_expression)

    # low level release daily revenue (this assumes constant head, which is not important for now)
    def revenue_ll_def(m, t):
        return m.pi_ll[t] == 0.90 * m.head_ll * m.gamma * m.Qll[t] * m.base_load_price / 3600
    m.revenue_ll = Constraint(m.t, rule=revenue_ll_def)
    
    # daily hydropeaking revenue
    def revenue_day_def(m, t):
        return m.pi[t] == 0.90 * m.head * m.gamma * sum(m.Qph_h[t,h] * m.price[t,h] for h in m.h) / 3600 
    m.revenue_day = Constraint(m.d, rule=revenue_day_def)
    
    # multidaily hydropeaking revenue
    def revenue_multiday_def(m, t):
        return m.pi[t] == 0.90 * m.head * m.gamma * sum(m.Qph_piece[t,p] * m.rc_slope[t,p] for p in m.p) / 3600    
    m.revenue_multiday = Constraint(m.md, rule=revenue_multiday_def)
    
    # cost function
    def ifr_cost_day_def(m, t):        
        return m.C_ifr[t] == sum(m.C_ifr_low * m.Qifr_min_deficit_h[t,h] for h in m.h)
    m.ifr_cost_day = Constraint(m.d, rule=ifr_cost_day_def)
    
    def ifr_cost_multiday_def(m, t):
        return m.C_ifr[t] == m.C_ifr_low * m.Qifr_min_deficit[t]
    m.ifr_cost_multiday = Constraint(m.md, rule=ifr_cost_multiday_def)
    
    #def end_storage_def(m, t):
        #if t==m.t.last():
            #return m.B_S[t] == m.ESV * m.S[t]
        #else:
            #return m.B_S[t] == 0.0
    #m.end_storage = Constraint(m.t, rule=end_storage_def)
    
    # ============
    # mass balance
    # ============
    
    def mass_balance(m, t):
        return m.S[t] == m.Si[t] + m.Qin_assumed[t] - m.Qsp[t] - m.Qph[t] - m.Qll[t]
    m.mass_balance = Constraint(m.t, rule=mass_balance) 
    
    # ======
    # inflow
    # ======
    
    def assumed_inflow(m, t):
        return m.Qin_assumed[t] == m.Qin[t]
    m.inflow = Constraint(m.t, rule=assumed_inflow)
    
    # =================
    # reservoir storage
    # =================
    
    def initial_storage_def(m, t):
        if t==m.t.first():
            return m.Si[t] == m.S0
        else:
            return m.Si[t] == m.S[m.t.prev(t)]
    m.initial_storage = Constraint(m.t, rule=initial_storage_def)
    
    def initial_space_def(m, t):
        return m.S_space[t] == m.S_max - m.Si[t]
    m.initial_space = Constraint(m.t, rule=initial_space_def)
    
    # minimum reservoir storage
    def storage_min(m, t):
        return m.S[t] >= m.S_min
    m.storage_min = Constraint(m.t, rule=storage_min)
    
    # maximum reservoir storage
    def storage_max(m, t):
        return m.S[t] <= m.S_max
    m.storage_max = Constraint(m.t, rule=storage_max)
    
    #storage_max_decrease(t) "maximum daily reservoir storage decrease"
    #storage_max_increase(t) "maximum daily reservoir storage increase"
    #;
    
    #storage_max_decrease(d)..
    #S(d-1) - S(d) =l= dS_low_lim + dS_low(d) ;
    
    #storage_max_increase(d)..
    #S(d) - S(d-1) =l= dS_high_lim + dS_high(d) ;
    
    # ============
    # Spill logic
    # ============
    
    m.M1 = Param(initialize=1e6)
    m.M2 = Param(initialize=1e6)
    
    m.spill_switch = Var(m.t, domain=Binary)
    m.Qin_exc = Var(m.t, domain=Reals)
    m.Qsp_dummy = Var(m.t, domain=NonNegativeReals)

    # inflow in excess of existing reservoir capacity and controlled releases
    def inflow_excess_def(m, t):
        return m.Qin_exc[t] == m.Qin_assumed[t] - (m.S_space[t] + m.Qph[t] + m.Qll[t])
    m.inflow_exces = Constraint(m.t, rule=inflow_excess_def)
    
    # ensure spill does not exceed excess inflow
    def spill_limit(m, t):
        return m.Qsp[t] - m.Qsp_dummy[t] == m.Qin_exc[t]
    m.spill_limit = Constraint(m.t, rule=spill_limit)
    
    # spill constraint part 1
    def spill_switch_1(m, t):
        return m.Qsp[t] <= m.M1 * m.spill_switch[t]
    m.spill_switch_1 = Constraint(m.t, rule=spill_switch_1)
             
    # spill constraint part 2
    def spill_switch_2(m, t):
        return m.Qsp_dummy[t] <= m.M2 * (1 - m.spill_switch[t])
    m.spill_switch_2 = Constraint(m.t, rule=spill_switch_2)
    
    # =========================
    # Instream flow requirement
    # =========================
    
    # note: the IFR should be hourly to ensure that all hours have MIF
    # i.e., to prevent dessication in some hours for hydropower generation
    # later. See Olivares and Lund (2012).
    
    # minimum hourly flow
    def ifr_min_h(m, t, h):
        return m.Qll_h[t,h] + m.Qifr_min_deficit_h[t,h] >= m.Qifr_min / 24.0
    m.ifr_min_h = Constraint(m.dh, rule=ifr_min_h)
    
    # minimum multiday flow
    def ifr_min(m, t):
        return m.Qll[t] + m.Qifr_min_deficit[t] >= m.Qifr_min * m.ndays[t]
    m.ifr_min = Constraint(m.md, rule=ifr_min)
    
    # ==========
    # Powerhouse
    # ==========
    
    # hourly powerhouse balance
    def ph_hourly_balance(m, t):
        return sum(m.Qph_h[t,h] for h in m.h) == m.Qph[t]
    m.ph_hourly_balance = Constraint(m.d, rule=ph_hourly_balance)
    
    # piecewise piece multiday mass balance
    def ph_multiday_balance(m, t):
        return sum(m.Qph_piece[t,p] for p in m.p) == m.Qph[t]
    m.ph_multiday_balance = Constraint(m.md, rule=ph_multiday_balance)
    
    # piecewise piece maximum capacity
    def ph_piece_range(m, t, p):
        return m.Qph_piece[t,p] <= m.rc_range[t,p] * m.Qph_max * m.ndays[t]
    m.ph_piece_range = Constraint(m.mdp, rule=ph_piece_range)
    
    # hourly powerhouse capacity
    def ph_hourly_capacity(m, d, h):
        return m.Qph_h[d,h] <= m.Qph_max / 24.0
    m.ph_hourly_capacity = Constraint(m.dh, rule=ph_hourly_capacity)
    
    # day and multiday powerhouse capacity
    def ph_capacity(m, t):
        return m.Qph[t] <= m.Qph_max * m.ndays[t]
    m.ph_capacity = Constraint(m.t, rule=ph_capacity)
    
    # ================
    # low level outlet
    # ================
    
    # low level outlet daily (multihour) mass balance
    def ll_hourly_balance(m, t):
        return sum(m.Qll_h[t,h] for h in m.h) == m.Qll[t]
    m.ll_hourly_balance = Constraint(m.d, rule=ll_hourly_balance)
    
    # low level outlet hourly capacity
    def ll_hourly_capacity(m, t, h):
        return m.Qll_h[t,h] == m.Qll_max/24.0
    m.ll_hourly_capacity = Constraint(m.dh, rule=ll_hourly_capacity)
    
    # low level outlet capacity (all time steps)
    def ll_capacity(m, t):
        return m.Qll[t] <= m.Qll_max * m.ndays[t]
    m.ll_capacity = Constraint(m.t, rule=ll_capacity)
    
    
    return m

def update_instance(instance, S0, inflow, prices, tslens, rcurve_ranges, rcurve_slopes):
    
    # update initial conditions
    if S0==None:
        S0 = 0
    getattr(instance, 'S0').set_value(S0)
    
    # update boundary conditions (hydrology)
    for key in inflow.keys():
        getattr(instance, 'Qin')[key] = inflow[key]
    
    # update prices
    for key in prices.keys():
        getattr(instance, 'price')[key] = prices[key]
        
    # update time step lengths
    for key in tslens.keys():
        getattr(instance, 'ndays')[key] = tslens[key]
        
    # update revenue curves
    for key in rcurve_ranges.keys():
        getattr(instance, 'rc_range')[key] = rcurve_ranges[key]
    
    for key in rcurve_slopes.keys():
        getattr(instance, 'rc_slope')[key] = rcurve_slopes[key]
    
    return instance