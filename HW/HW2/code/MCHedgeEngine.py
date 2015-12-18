"""
Copyright: Copyright (C) 2015 Baruch College FX Modeling and Market Making
Description: This is including the class of MCHedgeEngine for HW2
Author: Zhenfeng Liang
Contact: zhenfeng.jose.liang@gmail.com
"""

from math import sqrt, exp
import numpy as np


class FXHedgePort:
    '''
    Portfolio including hedging benchmark and the stock you need to hedge.
    t: starting time
    T: settlement time of the forward
    T1: settlement time of benchmark 1
    T2: settlement time of benchmark 2
    '''
    def __init__(self, t, T, T1, T2):
        self.t = t
        self.T = T
        self.T1 = T1
        self.T2 = T2

class RateEvolver:
    '''
    Evolve rate to a future time dt.
    sigma1, sigma2, beta1, beta2, rho: model dynamics parameters
    dt: future time spot evolved to
    Q0: rate at the starting time
    port: portfolio object
    '''
    def __init__(self, sigma1, sigma2, beta1, beta2, rho, dt, Q0, port):
        '''
        Because the curve is flat, I am using the same T to cal shock coef.
        I let the same T to be the end of simulation 
        '''
        self.sigma1 = sigma1 * sqrt(dt)
        self.sigma2 = sigma2 * sqrt(dt)
        self.beta1 = beta1
        self.beta2 = beta2
        self.rho = rho
        self.dt = dt
        self.Q0 = Q0
        self.port = port
        self.initDynamicCoef()

    def __str__(self):
        return "This is a Model creator class."

    def initDynamicCoef(self):
        '''
        Calculate the model dynamics coefficient
        '''
        self.tilt_shock_coef = self.sigma1 * exp(-self.beta1 * self.port.T) + self.rho * self.sigma2 * exp(-self.beta2 * self.port.T)
        self.parallel_shock_coef = self.sigma2 * sqrt(1 - self.rho * self.rho) * exp(-self.beta2 * self.port.T)

        self.tilt_shock_coef1 = self.sigma1 * exp(-self.beta1 * self.port.T1) + self.rho * self.sigma2 * exp(-self.beta2 * self.port.T1)
        self.parallel_shock_coef1 = self.sigma2 * sqrt(1 - self.rho * self.rho) * exp(-self.beta2 * self.port.T1)

        self.tilt_shock_coef2 = self.sigma1 * exp(-self.beta1 * self.port.T2) + self.rho * self.sigma2 * exp(-self.beta2 * self.port.T2)
        self.parallel_shock_coef2 = self.sigma2 * sqrt(1 - self.rho * self.rho) * exp(-self.beta2 * self.port.T2)        
        
    def GetQ(self):
        '''
        Evolved the asset currency interest rate.
        
        Return:
        Q: exposure forward tenor rate
        Q1: benchmark 1 tenor rate
        Q2: benchmark 2 tenor rate
        '''
        z = np.random.randn(2)
        Q = self.Q0 + self.tilt_shock_coef * z[0] + self.parallel_shock_coef * z[1]
        Q1 = self.Q0 + self.tilt_shock_coef1 * z[0] + self.parallel_shock_coef1 * z[1]
        Q2 = self.Q0 + self.tilt_shock_coef2 * z[0] + self.parallel_shock_coef2 * z[1]
        
        return Q, Q1, Q2


class FXFwdCalculator:
    '''
    Foreign Exchange Forward Contract Calculator
    '''

    def calVal(self, S, Q, R, t, T, K):
        '''
        Calculate the price of the forward contract
        '''
        return S * exp(-Q * (T - t)) - K * exp(-R * (T - t))
    
    def calFairStrike(self, S, Q, R, t, T):
        '''
        Calculate the fair strike of a forward contract
        '''
        return S * exp((R - Q) * (T - t))


class MCHedgeEngine:
    '''
    The engine to run MC to see performance of different hedge methods
    '''

    def __init__(self, rateEvolver, port):
        self.fxFwd = FXFwdCalculator()
        self.rateEvolver = rateEvolver
        self.port = port
        self.initTriangleShockNotionals()
        self.initTwoFactorShockNotionals()
           
    def runMC(self, numPath, S, R):
        '''
        S: spot rate
        R: denominate currency interest rate
        Return:
        unHedged: value vector of unhedged portfolio 
        triHedged: triangle hedge vector
        factorHedged: factor hedge vector
        ''' 
        self.fairK = self.fxFwd.calFairStrike(S, self.rateEvolver.Q0, R, self.port.t, self.port.T)
        self.fairK1 = self.fxFwd.calFairStrike(S, self.rateEvolver.Q0, R, self.port.t, self.port.T1)
        self.fairK2 = self.fxFwd.calFairStrike(S, self.rateEvolver.Q0, R, self.port.t, self.port.T2)
         
        unHedged = np.zeros(numPath)
        triHedged = np.zeros(numPath)
        factorHedged = np.zeros(numPath)

        for i in range(0, numPath):
            QEvolved, Q1Evolved, Q2Evolved = self.rateEvolver.GetQ()
            start_t = self.port.t + self.rateEvolver.dt
            unHedged[i] = self.fxFwd.calVal(S, QEvolved, R, start_t, self.port.T, self.fairK)
            triHedged[i] = unHedged[i] \
                           - self.triN1 * self.fxFwd.calVal(S, Q1Evolved, R, start_t, self.port.T1, self.fairK1) \
                           - self.triN2 * self.fxFwd.calVal(S, Q2Evolved, R, start_t, self.port.T2, self.fairK2)

            triHedged[i] = unHedged[i] \
                           - self.triN1 * self.fxFwd.calVal(S, Q1Evolved, R, start_t, self.port.T1, self.fairK1) \
                           - self.triN2 * self.fxFwd.calVal(S, Q2Evolved, R, start_t, self.port.T2, self.fairK2)

            factorHedged[i] = unHedged[i] \
                              - self.facN1 * self.fxFwd.calVal(S, Q1Evolved, R, start_t, self.port.T1, self.fairK1) \
                              - self.facN2 * self.fxFwd.calVal(S, Q2Evolved, R, start_t, self.port.T2, self.fairK2)

        return unHedged, triHedged, factorHedged

    def comparePerformance(self, numPath, S, R):
        unHedged, triHedged, factorHedged = self.runMC(numPath, S, R)
        print "UnHedged sd is", unHedged.std()
        print "TriHedged sd is", triHedged.std()
        print "FactorHedged sd is", factorHedged.std()
        print "\n"

    def initTriangleShockNotionals(self):
        '''
        Calculate notionals of triangle shock
        '''
        T = self.port.T
        T1 = self.port.T1
        T2 = self.port.T2
        Q0 = self.rateEvolver.Q0
        
        if T1 < T and T < T2:
            self.triN1 = (T2 - T) / (T2 - T1) * T / T1 * exp(-Q0 * (T - T1))
            self.triN2 = (T - T1) / (T2 - T1) * T / T2 * exp(Q0 * (T2 - T))
        elif T <= T1:
            self.triN1 = T / T1 * exp(-Q0 * (T - T1))
            self.triN2 = 0
        elif T >= T2:
            self.triN1 = 0
            self.triN2 = T / T2 * exp(-Q0 * (T - T2))

    def initTwoFactorShockNotionals(self):
        '''
        Calculate notionals of a two factor model shock
        '''
        T = self.port.T
        T1 = self.port.T1
        T2 = self.port.T2
        Q0 = self.rateEvolver.Q0        
        beta1 = self.rateEvolver.beta1
        beta2 = self.rateEvolver.beta2

        if T == T1:
            self.facN1 = 1
            self.facN2 = 0
        elif T == T2:
            self.facN1 = 0
            self.facN2 = 1
        else:
            a = T1 / T * exp(-(beta1 + Q0) * (T1 - T))
            b = T2 / T * exp(-(beta1 + Q0) * (T2 - T))
            c = T1 / T * exp(-(beta2 + Q0) * (T1 - T))
            d = T2 / T * exp(-(beta2 + Q0) * (T2 - T))
            self.facN1 = (b - d) / (b * c - a * d)
            self.facN2 = (c - a) / (b * c - a * d)

