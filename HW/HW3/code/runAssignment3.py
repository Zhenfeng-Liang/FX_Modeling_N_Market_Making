'''
This is a script set up for the FX Modeling and Market Making Assignment 3.
'''

from Spliner import Spliner
from scipy import *
import scipy.stats as stats
import matplotlib.pyplot as plot



def runAssignment3():
    '''This is set up for the assignment 3 test'''
    
    Spot = 1.0 
    ATM = 0.08
    Rr25 = 0.01
    Rr10 = 0.018
    Bf10 = 0.008
    Bf25 = 0.0025
    Texp = 0.5

    F_vec = [0.01, 10]
    for extrap_F in F_vec:        
        
        sp = Spliner(Spot, ATM, Rr25, Rr10, Bf10, Bf25, Texp, extrap_F)

        # set up for the plot axis
        strike_min = sp.StrikeMin
        strike_max = sp.StrikeMax        
        strikesNum = 100
        strikesDist = (strike_max-strike_min)/(strikesNum-1)
        
        strikes_vec, vols_vec = [], []
        for i in range(strikesNum):
            strike = strike_min + i * strikesDist
            strikes_vec.append(strike)
            vols_vec.append(sp.volatility(strike)*100)
            
        # Plotting on the same graph
        plot.plot(strikes_vec,vols_vec)

    plot.show()


if __name__=="__main__":
    runAssignment3()
