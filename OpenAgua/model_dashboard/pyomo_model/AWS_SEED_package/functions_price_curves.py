# this script creates monthly release-revenue curves for a given price
# time series and creates several plots
import csv, sys, math, numpy as np, datetime as dt, pandas as pd
from collections import OrderedDict
from os import path

# sum of squares
def ss(x, y):
    return np.sum((x-y)**2)

# squareroot sum of squares
def rootss(x, y):
    return math.sqrt(np.sum((x-y)**2))

# sum of differences
def sumdiff(x, y):
    return np.sum(x-y)

def linearizeOneCurve(curve, tol=0.001, maxiter=20):
    
    delta = len(curve) / 2
    i = delta
    
    iteration = 0
    
    escape = False
    
    X, Y = zip(*curve)
    X = np.array(X)
    Y = np.array(Y)
    
    while escape != True:
        iteration += 1
        
        m = (Y[-1] - Y[0]) / (X[-1] - X[0])
        b = Y[0]
        linearY = m * (X - X[0]) + b
        
        ssL = ss(Y[:i], linearY[:i])
        ssR = ss(Y[i:], linearY[i:])
        
        eps = abs((ssL - ssR) / ssL)
        if eps < tol or iteration == maxiter:
            escape = True
        else:
            delta /= 2
            if ssL < ssR:
                i = i + delta
            else:
                i = i - delta
    
    return i, (X[i], Y[i])
    

def linearizeCurve(curve, N, newPoints, main=False):
    
    if main:
        newPoints = [curve[0]]
    
    #n = int(math.log(N, 2))
    
    #ranges = {}
    #for i in range(n):
        
    idxMid, ptMid = linearizeOneCurve(curve)
    
    if N > 2:
    
        newPoints = linearizeCurve(curve[:idxMid], N / 2, newPoints)
        
        newPoints = linearizeCurve(curve[idxMid:], N / 2, newPoints)
        
    newPoints.append(ptMid)
            
    if main:
        newPoints.append((curve[-1]))
        newPoints.sort()
        
        x, y = zip(*newPoints)
        x = np.array(x)
        y = np.array(y)
        
        return x, y
        
    else:
        return newPoints

def create_revenue_curve(prices_df, npieces=8):
    # n should be an integer power of 2 (2, 4, 8, 16, etc.) 
    # the general approach is to create linear parts of equal R^2 between line and associated curve part
    
    ts = prices_df.stack().values
    #ts = np.sort(ts)
    
    # create the curve
    perc = np.arange(101, dtype=float)
    cap = perc.copy()
    freq = np.array([np.percentile(ts, p) for p in perc[::-1]])
    rev = np.cumsum(freq)
    curve = zip(cap, rev)
    cap, rev = zip(*linearizeCurve(curve, npieces, [], main=True))
    cap = np.array(cap)
    
    rc_ranges, rc_slopes = [], []
    for i in range(1,len(cap)):
        rc_range = cap[i] - cap[i-1]
        rc_slope = (rev[i] - rev[i-1]) / rc_range
        rc_ranges.append(rc_range / 100.0)
        rc_slopes.append(rc_slope)

    # return
    return rc_ranges, rc_slopes

def find_nearest(array, value, offset=0):
    array = np.array(array)
    idx = (np.abs(array-value)).argmin()
    return array[min(max(idx+offset, 0), len(array) - 1)]

def create_revenue_curve2(prices_df, method='optimized', npieces=8, interval=None):
    # linear parts n can be any number  
    # the general approach is to segment by curve slope thresholds, with n segments (n-1 breakpoints)
    # this is essentially an on/off peak approach, with greater (>2) resolution, consistent with
    # PG&E's approach
    
    ts = sorted(prices_df.stack().values)[::-1]
    
    # create the frequency curve
    N = float(len(ts))
    
    cap = np.arange(N+1) / N
    rev = np.cumsum([0.] + ts) / N * 100.    
    
    if method=='optimized':
        
        ts = [0.] + ts
        cap = np.arange(N+1.) / N
        rev = np.cumsum(ts) / N * 100.
        lincap, linrev = linearizeCurve(zip(cap, rev), npieces, [], main=True)

    if method=='intervals':
        
        breakpoints = range(500, -100, -interval)
        
        # revenue & capacity (as percent of maximum)
        lincap = np.array([0] + [sum(1. for x in ts if x >= bp) for bp in breakpoints]) / N
        linrev = np.array([0] + [sum(x for x in ts if x >= bp) for bp in breakpoints]) / N * 100.
        
    #lincap = lincap / N
    #linrev = linrev / N * 100.
        
    # calculate ranges and slopes
    rc_ranges = lincap[1:] - lincap[:-1]
    rc_vals = linrev[1:] - linrev[:-1]
    rc_slopes = rc_vals / (rc_ranges * 100.)

    rc_slopes[rc_ranges==0.] = 0.

    # return
    return rc_ranges, rc_slopes