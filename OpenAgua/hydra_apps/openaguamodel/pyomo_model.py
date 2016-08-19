from __future__ import division
from pyomo.core import *

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
    
    