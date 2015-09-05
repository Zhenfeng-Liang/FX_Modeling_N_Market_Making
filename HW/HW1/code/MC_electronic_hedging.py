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


def simulate_one_path(paras_dict):

    S0 = paras_dict['S0']
    sigma = paras_dict['sigma']    
    trade_size = paras_dict['trade_size']
    prob_long_trade = paras_dict['prob_long_trade']
    client_trade_spread = paras_dict['client_trade_spread']
    hedge_trade_spread = paras_dict['hedge_trade_spread']
    delta_limit = paras_dict['delta_limit'] 
    hedge_target = paras_dict['hedge_target']
    prob_trade = paras_dict['prob_trade']
    time_steps = paras_dict['time_steps']
    sigma_dt = paras_dict['sigma_dt']
    

    dS = sigma_dt * np.random.randn(time_steps)
    
    # Cumsum each row, e.g each simulation path
    S = np.append(1, dS).cumsum()
    
    trade_size_mat = np.where( np.random.rand(time_steps + 1) < prob_trade, trade_size, 0 )
    long_short_mat = np.where( np.random.rand(time_steps + 1) < prob_long_trade, 1, -1 )
    trade_size_mat = trade_size_mat * long_short_mat
    del long_short_mat
    

    pnl_vec = S * np.absolute(trade_size_mat) * client_trade_spread * 0.5
    
    pos = np.zeros(time_steps + 1)
    
    #paid_pnl = 0
    for i in range(time_steps + 1):
        # Note the little trick here. I get pos[i-1] is the last element of the pos which is zero. This makes the formula neater.
        pos[i] = pos[i-1] + trade_size_mat[i]
        
        if fabs(pos[i]) > fabs(delta_limit):

            hedge_notional = fabs(pos[i]) - fabs(hedge_target)
            pnl_vec[i] = hedge_trade_spread * S[i] * hedge_notional * 0.5
            if pos[i] > 0:
                pos[i] = hedge_target
            else:
                pos[i] = -1 * hedge_target
                

    pnl_vec[1:len(pnl_vec)] += pos[:len(pos)-1] * dS
    
    pnl_mean = pnl_vec.mean()
    pnl_std = pnl_vec.std()
    sharp_ratio = pnl_mean/pnl_std
    print "Pnl mean: ", pnl_mean, "\nPnl std: ", pnl_std, "\nSharp ratio: ", sharp_ratio

    return pnl_mean, pnl_std, sharp_ratio


def MC_trigger(paras_dict):
    
    num_paths = paras_dict['num_paths']
    dt_sec = 0.1 / paras_dict['_lambda_']  # seconds
    paras_dict['prob_trade'] =  1 - exp(-1 * paras_dict['_lambda_'] * dt_sec)
    dt = dt_sec / (paras_dict['trading_days_per_year'] * 24 * 60 * 60)
    paras_dict['sigma_dt'] = sqrt(dt) * paras_dict['sigma']

    mean_sum = 0
    std_sum = 0
    sharp_ratio_sum = 0
    for i in range(num_paths):
        print "path ", i
        mean_i, std_i, sharp_ratio_i = simulate_one_path(paras_dict)
        mean_sum += mean_i
        std_sum += std_i
        sharp_ratio_sum += sharp_ratio_i
    
    print "\nMC result:\nmc_mean: ", mean_sum / num_paths, "\nmc_std: ", std_sum / num_paths, "\nmc_sharp_ratio: ", sharp_ratio_sum / num_paths
        
    return 


def main():
    
    paras_dict = {'S0' : 1, 'sigma' : 0.1, '_lambda_' : 1, 'trade_size' : 1, 'prob_long_trade' : 0.5, 'client_trade_spread' : 0.0001, 'hedge_trade_spread' : 0.0002, 'delta_limit' : 0.5, 'hedge_target' : 0, 'time_steps' : 100, 'num_paths' : 10, 'trading_days_per_year' : 260}

    MC_trigger(paras_dict)

    return



if __name__=="__main__":
    main()
