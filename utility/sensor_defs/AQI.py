#!/usr/bin/python3
## \file AQI.py EPA Air Quality Index calculations

from bisect import bisect_left

# EPA Air Quality Index category breakpoints
EPA_AQI_Y       = [0.,  50.,    100.,   150.,   200.,   300.,   400.,   500.]
# EPA PM2.5 ug/m^3 -> AQI breakpoints
EPA_PM25_AQI_X  = [0.,  12.,    35.5,   55.5,   150.5,  250.5,  350.5,  500.]
# EPA PM10 ug/m^3 -> AQI breakpoints
EPA_PM10_AQI_X  = [0.,  55.,    155.,   255.,   355.,   425.,   505.,   605.]

def piecewise_linear_intperl(X, Y, x):
    if x <= X[0]: return Y[0]
    if x >= X[-1]: return Y[-1]
    i = bisect_left(X, x)
    l = (x-X[i-1])/(X[i] - X[i-1])
    return Y[i-1]*(1-l) + Y[i]*l

def PM25_to_AQI(x): return piecewise_linear_intperl(EPA_PM25_AQI_X, EPA_AQI_Y, x)
