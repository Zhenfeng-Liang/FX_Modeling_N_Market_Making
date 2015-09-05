'''
Copyright (c) 2015 Zhenfeng Liang, Baruch College 
Created on Sep 1, 2015
@author: Zhenfeng Liang
@contact: zhenfeng.jose.liang@gmail.com
@description: main function to run a monte carlo to simulate electronic hedging 
@usage: 
'''

# 3rd part imports 
import numpy as np
from math import exp, sqrt, fabs

def MC_trigger(num_paths):


    S0 = 1
    sigma = 0.1 # per year
    _lambda_ = 1 # trade per second
    trade_size = 1
    prob_long_trade = 0.5
    client_trade_spread = 0.0001
    hedge_trade_spread = 0.0002
    
    delta_limit = 2  # units, assuming it is positive 
    hedge_target = 1

    dt_sec = 0.1 / _lambda_  # seconds
    prob_trade = 1 - exp(-_lambda_ * dt_sec)
    time_steps = 100

    trading_days_per_year = 260
    dt = dt_sec / (trading_days_per_year * 24 * 60 * 60)

    sigma_dt = sqrt(dt) * sigma
    
    dS = sigma_dt * np.random.randn(time_steps)

    
    # Cumsum each row, e.g each simulation path
    S = np.append(1, dS).cumsum()
    
    trade_size_mat = np.where( np.random.rand(time_steps + 1) < prob_trade, trade_size, 0 )
    long_short_mat = np.where( np.random.rand(time_steps + 1) < prob_long_trade, 1, -1 )
    trade_size_mat = trade_size_mat * long_short_mat
    del long_short_mat

    received_pnl = S.dot(np.absolute(trade_size_mat)) * client_trade_spread * 0.5
    print "Received pnl is ", received_pnl
    
    pos = np.zeros(time_steps + 1)
     
    paid_pnl = 0
    for i in range(time_steps + 1):
        # Note the little trick here. I get pos[i-1] is the last element of the pos which is zero. This makes the formula neater.
        pos[i] = pos[i-1] + trade_size_mat[i]
        
        if fabs(pos[i]) > fabs(delta_limit):
            print "Before hedged: ", pos[i]

            hedge_notional = fabs(pos[i]) - fabs(hedge_target)
            paid_pnl += hedge_trade_spread * S[i] * hedge_notional * 0.5
            if pos[i] > 0:
                pos[i] = hedge_target
            else:
                pos[i] = -1 * hedge_target
                
            print "After hedged: ", pos[i]
        
    print "Paid pnl", paid_pnl

    pos_pnl = pos[:len(pos)-1].dot(dS)
    
    print "position pnl is ", pos_pnl

    total_pnl = received_pnl - paid_pnl + pos_pnl

    print "Total PNL is ", total_pnl

    
    return


def main():
    MC_trigger(1)

    return



if __name__=="__main__":
    main()
