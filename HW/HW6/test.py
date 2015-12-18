"""
  Copyright: Copyright (C) 2015 Baruch College - FX modeling

  Author: Zhenfeng Liang, Zhenfeng.Jose.Liang@gmail.com

  Created on: Oct 16, 2015

  Description: this is for FX modeling HW6. Plot dual digital price with respect to rho

  All Copyrights (C) Reserved
"""

from time import time


import scipy as sp
from scipy.stats import norm

import matplotlib.pyplot as plt
import numpy as np

from scipy.integrate import dblquad

def dualDigiPriceAnalytics(p1, p2):
    
    start = time()
    x1k = norm.ppf(1 - p1)
    x2k = norm.ppf(1 - p2)
    
    def jointDensity(y, x, rho):
        scale = 1 / (2 * sp.pi * sp.sqrt(1 - rho * rho))
        expo = sp.exp(-(y ** 2 + x ** 2 - 2 * rho * y * x) / (2 * (1 - rho ** 2)))
        return (scale * expo)
      
    calPrice = lambda rho : dblquad(jointDensity, x2k, sp.inf, lambda x : x1k, lambda x : sp.inf, args=(rho,))[0]

    rhoVec = np.linspace(-.99, .99, num=61)

    opsPrice = [calPrice(rho) for rho in rhoVec]
    
    end = time()

    print "time: ", end - start
    plt.plot(rhoVec, opsPrice)
    
    plt.title("Dual digital option price and correlation rho")
    plt.xlabel("Correlation (rho)")
    plt.ylabel("Option Price ($)")
    
    plt.show()
    

    return




p1 = .65
p2 = .30
dualDigiPriceAnalytics(p1, p2)




