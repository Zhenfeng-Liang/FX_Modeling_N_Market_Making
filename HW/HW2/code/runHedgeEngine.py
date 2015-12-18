"""
Copyright: Copyright (C) 2015 Baruch College FX Modeling and Market Making
Description: main function to run the hedge engine
Author: Zhenfeng Liang
Contact: zhenfeng.jose.liang@gmail.com
"""

# My own module
from MCHedgeEngine import *


def wrapForOneT(T, numPath):
    '''
    Wrapper for a tenor, T
    '''
    sigma1 = 0.01
    sigma2 = 0.008
    beta1 = 0.5
    beta2 = 0.1
    rho = -0.4
    dt = 0.001
    t = 0.0
    T1 = 0.25
    T2 = 1.0
    Q0 = 0.03
    R0 = 0.0
    S = 1.0

    port = FXHedgePort(t, T, T1, T2)    
    evor = RateEvolver(sigma1, sigma2, beta1, beta2, rho, dt, Q0, port)    
    MCEng1 = MCHedgeEngine(evor, port)
    print "T =", T
    MCEng1.comparePerformance(numPath, S, R0)
    

def main():

    numPath = 10000
    T_vec = [0.1, 0.25, 0.5, 0.75, 1.0, 2.0]
    print "Number of path is", numPath
    for T in T_vec:
        wrapForOneT(T, numPath)


if __name__ == '__main__':
    main() 
