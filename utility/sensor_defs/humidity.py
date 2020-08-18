#!/usr/bin/python3
## \file humidity.py Humidity calculations

from math import *

# Water vapour saturation pressure, valid between 0°C and 373°C
# W. Wagner and A. Pruß:" The IAPWS Formulation 1995 for the Thermodynamic Properties
# of Ordinary Water Substance for General and Scientific Use ",
# Journal of Physical and Chemical Reference Data, June 2002 ,Volume 31, Issue 2, pp. 387535:

def Water_Saturation_Vapor_Pressure(T):
    """Water vapour saturation pressure, in mbar, at T in Kelvin"""
    T_c = 647.096   # critical temperature, K
    P_c = 220640    # critical pressure, mbar
    u = 1. - T/T_c

    C1 =  -7.85951783
    C2 =   1.84408259
    C3 = -11.7866497
    C4 =  22.6807411
    C5 = -15.9618719
    C6 =   1.80122502

    C = C1*u + C2*u**1.5 + C3*u**3 + C4*u**3.5 + C5*u**4 + C6*u**7.5
    return P_c * exp(C*T_c/T)

def Ice_Saturation_Vapor_Pressure(T):
    """Saturation vapor pressure in mbar over ice at temperature T Kelvin"""
    Tn = 273.16     # triple point temperature, K
    Pn = 6.11657    # triple point pressure, mbar
    u = T/Tn

    a0 =-13.928169
    a1 = 34.707823

    return Pn * exp(a0*(1-u**-1.5) + a1*(1-u**-1.25))

def RH_to_Abs_Humidity(RH, T_in_C):
    """Absolute humidity [g/m^3], given relative humidity [%] and temperature [C]; ideal gas approx"""
    T_in_K = T_in_C + 273.15
    Pws = Water_Saturation_Vapor_Pressure(T_in_K) if T_in_C > 0 else Ice_Saturation_Vapor_Pressure(T_in_K)
    Pw = Pws * RH          # vapor pressure in Pa

    C = 2.16679            # g*K/J
    return C * Pw / T_in_K # g/m^3

def Pws_approx(T):
    """Approximation for water saturation vapor pressure [mbar], for T in C"""
    assert -20 <= T <= 50 # good to 0.083% in this range

    A = 6.116441
    m = 7.591386
    Tn = 240.7263
    return A*10**(m*T/(T + Tn))

def dewpoint(T, RH):
    """Dewpoint [C] as a function of relative humidity [mbar], using Pws_approx"""
    A = 6.116441
    m = 7.591386
    Tn = 240.7263
    Pw = Pws_approx(T)*RH/100.
    return Tn/(m/log10(Pw/A) - 1)

def heat_index(T, RH):
    """`Feels-like` temperature [C] given T in C, relative humidity in %"""
    c1 = -8.78469475556
    c2 =  1.61139411
    c3 =  2.33854883889
    c4 = -0.14611605
    c5 = -0.012308094
    c6 = -0.0164248277778
    c7 =  0.002211732
    c8 =  0.00072546
    c9 = -0.000003582
    T2 = T*T
    R2 = RH*RH
    return c1 + c2*T + c3*RH + c4*T*RH + c5*T2 + c6*R2 + c7*RH*T2 + c8*T*R2 + c9*T2*R2
