
from math import sqrt
from math import exp
import numpy as np

def calVega(S0, sigma, T):
    d1 = sigma * sqrt(T) / 2
    return S0 /sqrt(2 * np.pi) * exp(- d1 * d1 / 2) * sqrt(T)

def prob4(): 
    T = 0.5
    S1 = 1.25
    S2 = 1.56
    Sx = S1 / S2
    sigma1 = 0.085
    sigma2 = 0.075
    sigmax = 0.035
    vega1 = calVega(S1, sigma1, T)
    vega2 = calVega(S2, sigma2, T)
    vegax = calVega(Sx, sigmax, T)
    print "vega1: ", vega1 
    print "vega2: ", vega2
    print "vegax: ", vegax
    
    rho = (sigma1**2 + sigma2**2 - sigmax**2)/(2 * sigma1 * sigma2)
    print "rho:", rho
    N1 = - vegax/vega1 * (sigma1 - rho * sigma2) / sqrt(sigma1**2 + sigma2**2 - 2 * sigma1 * sigma2 * rho)
    N2 = - vegax/vega2 * (sigma2 - rho * sigma1) / sqrt(sigma1**2 + sigma2**2 - 2 * sigma1 * sigma2 * rho)
    print "N1:", N1, "N2:", N2


if __name__ == '__main__':
    prob4()
