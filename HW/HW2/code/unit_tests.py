"""
Copyright: Copyright (C) 2015 Baruch College FX Modeling and Market Making
Description: Unit tests script
Author: Zhenfeng Liang
Contact: zhenfeng.jose.liang@gmail.com
"""

# My own module
from MCHedgeEngine import *


def tests():

    sigma1 = 0.01
    sigma2 = 0.008
    beta1 = 0.5
    beta2 = 0.1
    rho = 0.4
    dt = 0.001
    T = 0.5
    t = 0
    T1 = 0.25
    T2 = 1

    Q0 = 0.03
    R0 = 0.0
    
    S = 1
    numPath = 1000

    port = FXHedgePort(t, T, T1, T2)    
    evor = RateEvolver(sigma1, sigma2, beta1, beta2, rho, dt, Q0, port)
    print evor.__str__()
    
    #print "dQ = ", evor.dQ_vec()
    print "QT = ", evor.GetQ()

    calculator = FXFwdCalculator()
    fairK = calculator.calFairStrike(S, Q0, R0, t, T)
    print "fairK = ", fairK
    print "One path value = ", calculator.calVal(S, evor.GetQ()[0], R0, t, T, fairK)


    MCEng1 = MCHedgeEngine(evor, port)
    unHedged, triHedged, factorHedged = MCEng1.runMC(numPath, S, R0)
    print "triN1 =", MCEng1.triN1, "triN2 =", MCEng1.triN2

    print "UnHedged PNL mean is", unHedged.mean(), "sd is", unHedged.std()
    print "TriHedged PNL mean is", triHedged.mean(), "sd is", triHedged.std()
    print "FactorHedged PNL mean is", factorHedged.mean(), "sd is", factorHedged.std()

if __name__ == '__main__':
    tests() # Run unittest
