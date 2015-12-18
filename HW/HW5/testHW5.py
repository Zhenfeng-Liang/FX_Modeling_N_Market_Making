"""
  Copyright: Copyright (C) 2015 Baruch College - FX modeling

  Author: Zhenfeng Liang, Zhenfeng.Jose.Liang@gmail.com

  Created on: Oct 13, 2015

  Description: this is for FX modeling HW5. Inverting characteristic function for jump diffusion model, compare it with the conditioned expectation method  

  All Copyrights (C) Reserved
"""

import scipy as sci
from scipy.integrate import quad
from scipy.stats import norm
import math
import matplotlib.pyplot as plt

import numpy as np

def calMu(S0, T, fwd_pts, r, sig, J_al, J_v, lam):
    '''
    Calibrate mu, let E(S_T) = F(T)
    '''    
    F = S0 + fwd_pts
    
    res = sci.log(F / S0)
    
    res = res - lam * T * sci.exp(J_al + J_v / 2)
    
    res = res + (lam - sig * sig / 2) * T
    
    res = res / T
    
    return res


### Function 1 to calculate call option price from the characteristic function
def calCallPriceCharacteristic(S0, T, fwd_pts, r, sig, J_al, J_v, lam, K):
    '''
    Inverting characteristic function
    '''
    F = S0 + fwd_pts
    x = sci.log(S0)
    
    mu = calMu(S0, T, fwd_pts, r, sig, J_al, J_v, lam)
    
    def A(theta):
        res = 1j * theta * mu * T
        res = res  - (theta * theta) * (sig * sig) * T / 2  
        res = res + lam *  T * (sci.exp(J_al * theta * 1j - (theta * theta) * J_v / 2) - 1)
        return res

    def f(theta):
        res = sci.exp(1j * theta * x + A(theta))
        return res

    def integrand(theta):
        
        res = f(theta) * sci.exp(-1j * theta * sci.log(K / S0))        
        res = res / (theta * theta + 1j * theta)
        
        return sci.real(res)

    tmp = 0 + 0j
    tmp, error = quad(integrand, 0, sci.inf)

    res = F - K / 2 - K / sci.pi * tmp.real
    
    res = res * sci.exp(-r * T) # Discounting
   
    return res


# Function 2 to calculate call option price from conditioned price
def calCallPriceCondN(S0, T, fwd_pts, r, sig, J_al, J_v, lam, K):
    '''
    Cal call price with BS with jumps by conditioning on the number of jumps
    '''
    mu = calMu(S0, T, fwd_pts, r, sig, J_al, J_v, lam)
    F = S0 + fwd_pts
    
    def calBSCallN(N):
        sigmaSquareT = sig ** 2 * T + N * J_v
        d1 = (sci.log(F / K) + 0.5 * sigmaSquareT) / sci.sqrt(sigmaSquareT)
        d2 = d1 - sci.sqrt(sigmaSquareT)
        res = (F * norm.cdf(d1) - K * norm.cdf(d2)) * sci.exp(-r * T)
        return res
            
    def calJProb(N):
        return (lam * T) ** N / math.factorial(N) * sci.exp(- lam * T)
    
    N_max = 30
    prob_sum = 0
    res = 0
    for i in xrange(0, N_max):
        bsPrice = calBSCallN(i)
        prob = calJProb(i)
        prob_sum = prob_sum + prob
        res = res + prob * bsPrice
        
    res = res / prob_sum
    
    return res
    

def impVolAnalytics(S0, T, fwd_pts, r, sig, J_al, J_v, lam):
    '''
    cal impled vol with inverting characteristic
    '''
    F = S0 + fwd_pts
    
    def blackScholes(vol,K):
        '''
        ordinary Black Scholes formula for calculating option price
        '''
        d1 = (sci.log(F/K)+0.5*vol*vol*T)/(vol*sci.sqrt(T))
        d2 = d1 - vol*sci.sqrt(T)
        callprice = sci.exp(-r*T)*(F*norm.cdf(d1)-K*norm.cdf(d2))
        return callprice

    def impliedVol(K):
        '''
        root finding process for method one
        '''
        func = lambda vol: ((blackScholes(vol,K) - calCallPriceCharacteristic(S0, T, fwd_pts, r, sig, J_al, J_v, lam, K)))
        impliedVol = sci.optimize.brentq(func,0.01,1.0)

        return impliedVol
        
    k = np.linspace(0.8,1.3,num=30)
    vols = []
    
    for i in k:
        vols.append(impliedVol(i))
    
    plt.plot(k,vols)
    plt.show()

    return
    

def testHW5():
    
    S0 = 1.0
    T = 0.5    
    fwd_pts = 0.03
    r = 0.05
    sig = 0.07
    J_al = -0.04
    J_v = 0.15 ** 2
    lam = 3.0
    K = 0.95
    
    
    print "Call price using inverse characteristic function:", calCallPriceCharacteristic(S0, T, fwd_pts, r, sig, J_al, J_v, lam, K)
    print "Call price using conditioned expectation:", calCallPriceCondN(S0, T, fwd_pts, r, sig, J_al, J_v, lam, K)
    
    impVolAnalytics(S0, T, fwd_pts, r, sig, J_al, J_v, lam)

    return 


if __name__ == '__main__':
    testHW5()
