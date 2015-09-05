'''
Copyright (c) 2015 Zhenfeng Liang, Baruch College 
Created on Sep 1, 2015
@author: Zhenfeng Liang
@contact: zhenfeng.jose.liang@gmail.com
@description: main function to run a Monte Carlo to simulate electronic hedging 
@usage: 
'''

# 3rd part imports 
import argparse
import numpy as np
import time
from math import exp, sqrt, fabs


def read_arg():
    '''
    @description: command line arguments parser
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument('-steps', action="store", default=500, type=int, help='time steps on each paths, default=500')
    parser.add_argument('-paths', action="store", default=1000, type=int, help='Number of paths you want to run, default=1000')    
    parser.add_argument('-target1', action="store", default=0, type=int, help='one hedged target(units), default=0')
    parser.add_argument('-target2', action="store", default=3, type=int, help='one hedged target(units), default=3')

    return parser.parse_args()


def simulate_one_path(paras_dict):
    '''
    @description: Calculates pnl, std, and sharp ratio for each path. It is mainly using vetorized operations. Another purely vetorized way to do this is to create a matrix with dimensions (num_paths, time_steps), instead of using a loop outside of this function. But the problem is when we need to calculate a lot of path, it will create a pretty big matrix which will definitely kill your machine soon. So, considering this situation, we use a vetorized operation only for a path.
    @paras_dict: a parameters dictionary
    @return: pnl_mean, std and sharp ratio for this path
    '''

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
    
    # Generate spot rate changes for each time step
    dS = sigma_dt * np.random.randn(time_steps)
    
    # Calculate the spot rate at each time point
    S = np.append(S0, dS).cumsum()
    
    # Generate a vector of trade size, when there is no trade, the element is 0, otherwise, there is the size of the trade
    trade_size_vec = np.where( np.random.rand(time_steps + 1) < prob_trade, trade_size, 0 )
    
    # Generate the long short vec
    long_short_vec = np.where( np.random.rand(time_steps + 1) < prob_long_trade, 1, -1 )
    
    # Get a trade size vec with direction
    trade_size_vec = trade_size_vec * long_short_vec
        
    # pnl from client spread
    pnl_vec = S * np.absolute(trade_size_vec) * client_trade_spread * 0.5
    
    # position vector
    pos = np.zeros(time_steps + 1)
    for i in range(time_steps + 1):
        # A little trick here. When i=0, pos[i-1] is the last element of the pos which is zero. This makes the formula neater.
        pos[i] = pos[i-1] + trade_size_vec[i]
        
        if fabs(pos[i]) > fabs(delta_limit):
            hedge_notional = fabs(pos[i]) - fabs(hedge_target)
            
            # Minus the pnl we need to pay to the inter-dealers, which is always positive except S<0 which is almost impossible
            pnl_vec[i] -= hedge_trade_spread * S[i] * hedge_notional * 0.5
            if pos[i] > 0:
                pos[i] = hedge_target
            else:
                pos[i] = -1 * hedge_target
                
    # Plus pnl from the exposure
    pnl_vec[1:len(pnl_vec)] += pos[:len(pos)-1] * dS
    
    # Get statistics
    pnl_mean = pnl_vec.mean()
    pnl_std = pnl_vec.std()
    sharp_ratio = pnl_mean/pnl_std

    return pnl_mean, pnl_std, sharp_ratio


def MC_trigger(paras_dict):
    '''
    @description: call MC, loop to calculate each path, cache common parameters for each path.
    @paras_dict: a parameters dictionary
    @return: sharp ratio of this Monte Carlo calculation
    '''

    # These are const variables for each path, cache outside of the loop
    dt_sec = 0.1 / paras_dict['_lambda_']  # seconds
    paras_dict['prob_trade'] =  1 - exp(-1 * paras_dict['_lambda_'] * dt_sec)
    dt = dt_sec / (paras_dict['trading_days_per_year'] * 24 * 60 * 60)
    paras_dict['sigma_dt'] = sqrt(dt) * paras_dict['sigma']

    mean_sum = 0
    std_sum = 0
    sharp_ratio_sum = 0

    num_paths = paras_dict['num_paths']

    # loop over each path
    for i in range(num_paths):
        mean_i, std_i, sharp_ratio_i = simulate_one_path(paras_dict)
        mean_sum += mean_i
        std_sum += std_i
        sharp_ratio_sum += sharp_ratio_i
    
    mc_pnl = mean_sum / num_paths
    mc_std = std_sum / num_paths
    mc_sharp_ratio = sharp_ratio_sum / num_paths

    return mc_sharp_ratio


def main():
    
    # Read arguments from command line and parse into the program
    args = read_arg()
    num_paths = args.paths
    time_steps = args.steps
    target1 = args.target1
    target2 = args.target2

    # Start timer
    start = time.time()

    # Initialize one set of parameters
    paras_dict1 = {'S0' : 1, 'sigma' : 0.1, '_lambda_' : 1, 'trade_size' : 1, 'prob_long_trade' : 0.5, 'client_trade_spread' : 0.0001, 'hedge_trade_spread' : 0.0002, 'delta_limit' : 3, 'hedge_target' : target1, 'time_steps' : time_steps, 'num_paths' : num_paths, 'trading_days_per_year' : 260}

    # Cal sharp ratio of the above set paras
    SR1 = MC_trigger(paras_dict1)

    # Initialize one set of parameters
    paras_dict2 = {'S0' : 1, 'sigma' : 0.1, '_lambda_' : 1, 'trade_size' : 1, 'prob_long_trade' : 0.5, 'client_trade_spread' : 0.0001, 'hedge_trade_spread' : 0.0002, 'delta_limit' : 3, 'hedge_target' : target2, 'time_steps' : time_steps, 'num_paths' : num_paths, 'trading_days_per_year' : 260}

    # Cal sharp ratio of the above set paras
    SR2 = MC_trigger(paras_dict2)

    print "Num paths:\t", num_paths, "\tTime steps:\t", time_steps
    print "When hedge target is ", target1, " SR is\t", SR1
    print "When hedge target is ", target2, " SR is\t", SR2    
    print "Time elapsed: ", time.time()-start, " seconds"


if __name__=="__main__":
    main()
