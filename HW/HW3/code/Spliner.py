"""
Author: Zhenfeng Liang
Description: Implemented a class to run the cubic spline for volatility
"""

import bisect
import math

from scipy import *
import scipy.stats as stats

class Spliner:
    '''
    A class to implement the cubic spliner. Given five benchmark data, it can construct a cubic spliner. The main function is Volatility.
    The main function is Volatility. Use this function to calculate the vol.
    '''
    
    def __init__(self, Spot, ATM, Rr25, Rr10, Bf10, Bf25, Texp, Extrap_F):
        self.Spot = Spot
        self.ATM = ATM
        self.Rr25 = Rr25
        self.Rr10 = Rr10
        self.Bf10 = Bf10
        self.Bf25 = Bf25
        self.Texp = Texp
        self.Extrap_F = Extrap_F

        # Initialization
        self.solveToInitialize()
        self.CSParams = self.InitializeCSParams()


    def volatility(self, strike):
        '''Function to do the interpolation given the strike'''
        
        # Coner cases, if the strike is outside of the range [StrikeMin, StrikeMax]
        if strike < self.StrikeMin:
            strike = self.StrikeMin
        
        if strike > self.StrikeMax:
            strike = self.StrikeMax
        
        # Start the interpolation
        
        # Find the index which the strike is sitting into
        ind = bisect.bisect_left(self.Strikes,strike)
        
        # Get the parameters of the spline
        a = self.CSParams[4*ind]
        b = self.CSParams[4*ind+1]
        c = self.CSParams[4*ind+2]
        d = self.CSParams[4*ind+3]
        
        # Returns the spline
        return a + b*strike + c*strike**2 + d*strike**3

    '''
    The following are the functions to initialize the spliner.
    '''
    def solveToInitialize(self):
        self.Vol10p = self.ATM - self.Rr10 / 2. + self.Bf10
        self.Vol25p = self.ATM - self.Rr25 / 2. + self.Bf25
        self.Vol25c = self.ATM + self.Rr25 / 2. + self.Bf25
        self.Vol10c = self.ATM + self.Rr10 / 2. + self.Bf10
        self.ATMStrike = self.Spot * exp(self.ATM**2 * self.Texp / 2.)
        self.Strike25c = self.Spot * exp(self.Vol25c**2 * self.Texp / 2. - self.Vol25c * sqrt(self.Texp) * stats.norm.ppf(0.25))
        self.Strike25p = self.Spot * exp(self.Vol25p**2 * self.Texp / 2. + self.Vol25p * sqrt(self.Texp) * stats.norm.ppf(0.25))
        self.Strike10c = self.Spot * exp(self.Vol10c**2 * self.Texp / 2. - self.Vol10c * sqrt(self.Texp) * stats.norm.ppf(0.10))
        self.Strike10p = self.Spot * exp(self.Vol10p**2 * self.Texp / 2. + self.Vol10p * sqrt(self.Texp) * stats.norm.ppf(0.10))

        # Store the benchmark as a vector
        self.Strikes = [self.Strike10p, self.Strike25p, self.ATMStrike, self.Strike25c, self.Strike10c]
        self.Vols = [self.Vol10p, self.Vol25p, self.ATM, self.Vol25c, self.Vol10c]
        
        self.StrikeMin = self.Strikes[0] * exp(-self.Extrap_F * self.Vols[0] * sqrt(self.Texp))
        self.StrikeMax = self.Strikes[-1] * exp(self.Extrap_F * self.Vols[-1] * sqrt(self.Texp))

        # Store all the strikes including the outside ones
        self.AllStrikes = [self.StrikeMin] + self.Strikes + [self.StrikeMax]


    def InitializeCSParams(self):
        '''Initialize the spliner parameters'''

        a = matrix(zeros((24,24)))
        b = matrix(zeros((24,1)))
        
        xs  = self.AllStrikes
        x2s = [x*x for x in xs]
        x3s = [x*x*x for x in xs]
        
        # Start calculating the coefficients of the spliner.
        for i in range(5):
            a[i,4*(i+1)] = 1
            a[i,4*(i+1)+1] = xs[i+1]
            a[i,4*(i+1)+2] = x2s[i+1]
            a[i,4*(i+1)+3] = x3s[i+1]
            
            b[i] = self.Vols[i]
        
        for i in range(5):
            a[i+5,4*i]       = 1
            a[i+5,4*i+1]     = xs[i+1]
            a[i+5,4*i+2]     = x2s[i+1]
            a[i+5,4*i+3]     = x3s[i+1]
            a[i+5,4*(i+1)]   = -1
            a[i+5,4*(i+1)+1] = -xs[i+1]
            a[i+5,4*(i+1)+2] = -x2s[i+1]
            a[i+5,4*(i+1)+3] = -x3s[i+1]
            
            b[i+5] = 0
        
        for i in range(5):
            a[i+10,4*i+1] = 1
            a[i+10,4*i+2] = 2*xs[i+1]
            a[i+10,4*i+3] = 3*x2s[i+1]
            a[i+10,4*(i+1)+1] = -1
            a[i+10,4*(i+1)+2] = -2*xs[i+1]
            a[i+10,4*(i+1)+3] = -3*x2s[i+1]
            
            b[i+10] = 0
        
        for i in range(5):
            a[i+15,4*i+2] = 2
            a[i+15,4*i+3] = 6*xs[i+1]
            a[i+15,4*(i+1)+2] = -2
            a[i+15,4*(i+1)+3] = -6*xs[i+1]
            
            b[i+15] = 0
        
        a[20,1] = 1
        a[20,2] = 2*xs[0]
        a[20,3] = 3*x2s[0]
        b[20]   = 0
        
        a[21,2] = 2
        a[21,3] = 6*xs[0]
        b[21]   = 0
        
        a[22,21] = 1
        a[22,22] = 2*xs[6]
        a[22,23] = 3*x2s[6]
        b[22]    = 0
        
        a[23,22] = 2
        a[23,23] = 6*xs[6]
        b[23]    = 0
        
        sol = a.I*b
        
        cs_params = [sol[i,0] for i in range(24)]
        
        return cs_params
