"""
Copyright: Copyright (C) 2014  Washington Square Technologies - All Rights Reserved
Description: Price a knockout option under a calibrated LVSV model
"""

import math
import scipy.optimize
import scipy.stats
#import wst.core.analytics.bs as bs
#import wst.core.analytics.fd as fd
#import wst.core.analytics.num as num
#import wst.core.analytics.payoff as payoff
#import wst.util.plot as plot

def cross_option_correlation_gamma(spot1,spot2,vol1,vol2,rho,strikex,texp):
    '''Calculates the "gamma" of a cross option to the implied correlation number.
    Assumes that interest rates are all zero.
    
    spot1:   spot of the USD pair ccy1-USD
    spot2:   spot of the USD pair ccy2-USD
    vol1:    vol of the USD pair ccy1-USD
    vol2:    vol of the USD pair ccy2-USD
    rho:     correlation between the two USD spots
    strikex: strike of the cross option ccy2-ccy1
    texp:    time to expiration
    '''
    
    rho_eps  = 1e-4 # size of rho tweak in the numerical partial derivatives
    volx_mid = math.sqrt(vol1*vol1+vol2*vol2-2*rho*vol1*vol2)
    volx_up  = math.sqrt(vol1*vol1+vol2*vol2-2*(rho+rho_eps)*vol1*vol2)
    volx_dn  = math.sqrt(vol1*vol1+vol2*vol2-2*(rho-rho_eps)*vol1*vol2)
    
    spotx    = spot1/spot2
    is_call  = strikex>=spotx
    optx_mid = bs.opt_price(is_call,spotx,strikex,texp,volx_mid,0,0)
    optx_up  = bs.opt_price(is_call,spotx,strikex,texp,volx_up, 0,0)
    optx_dn  = bs.opt_price(is_call,spotx,strikex,texp,volx_dn, 0,0)

    opt_corr_gamma = (optx_up+optx_dn-2*optx_mid)/rho_eps/rho_eps
    return opt_corr_gamma

def dual_digital_price(is_call,digi_price1,digi_price2,rho):
    '''Price of a dual digital using a Gaussian copula, given the regular digitals for the
    two assets. 
    
    is_call:     True for a digital call, False for a digital put; assumes that this applies to all three digitals
    digi_price1: European digital price for asset 1, call if is_call=True, put if is_call=False
    digi_price2: European digital price for asset 2, call if is_call=True, put if is_call=False
    rho:         Gaussian copula correlation
    '''
    
    # get the cumulative distribution values for the two assets; these should be digital
    # put prices
    
    F1 = digi_price1 if not is_call else 1-digi_price1
    F2 = digi_price2 if not is_call else 1-digi_price2
    
    # convert those to standard normals
    
    x1 = num.cnorminv(F1)
    x2 = num.cnorminv(F2)
    
    # calculate the joint distribution using the copula
    
    if is_call:
        _, dual_digi, _ = scipy.stats.mvn.mvndst([x1,x2],[0,0],[1,1],[rho])
    else:
        _, dual_digi, _ = scipy.stats.mvn.mvndst([0,0],[x1,x2],[0,0],[rho])
    
    return dual_digi

def calibrated_local_vols(spot,rd,rf,texps,strikes,imp_vols,alpha,beta,extrap_fact,nu,nt,nsd):
    '''Bootstraps the piecewise-constant local vol parameters in the LVSV model
    to match market implied vols.
    
    spot:        current spot price
    rd:          denominated discount rate (assumed equal for all tenors)
    rf:          asset discount rate (assumed equal for all tenors)
    texps:       list of times to expiration for the benchmark expirations
    strikes:     list of list of strikes: five strikes per benchmark expiration
    imp_vols:    list of list of implied vols: five vols per benchmark expiration
    alpha:       vol of vol model parameter
    beta:        mean reversion model parameter
    extrap_fact: cubic spline extrapolation parameter
    nu:          number of spot steps to use
    nt:          number of time steps to use
    nsd:         number of spot std devs to include in the spot direction
    '''
    
    volsdd = [] # x=-1.28
    volsd  = [] # x=-0.68
    vols0  = [] # x= 0
    volsu  = [] # x=+0.68
    volsuu = [] # x=+1.28
    
    break_times = [] # break times for local vols - equal to benchmark expiration times
    
    for i in range(len(texps)):
        time_strikes = strikes[i]
        time_vols    = imp_vols[i]
        
        def arg_func(vols):
            volsdd_new = volsdd+[vols[0]]
            volsd_new  = volsd +[vols[1]]
            vols0_new  = vols0 +[vols[2]]
            volsu_new  = volsu +[vols[3]]
            volsuu_new = volsuu+[vols[4]]
            
            break_times_new = break_times+[texps[i]]
            ntimes = len(vols0_new)
            
            if False:
                # this prices using backward induction - about 5x slower than forward induction as it
                # does a separate numerical pricing for each of the five options
                
                prices = []
                for strike in time_strikes:
                    bi = fd.LVSBICN(spot,volsdd_new,volsd_new,vols0_new,volsu_new,volsuu_new,[rd]*ntimes,[rf]*ntimes,break_times_new,alpha,beta,extrap_fact,nu,nt,nsd)
                    bi.initialize_payoff(payoff.OptionPayoff(True,strike),texps[i])
                    bi.go_back(0)
                    prices.append(bi.interp(spot))
            else:
                # this prices using forward induction - gets all five option prices in one analytics call
                
                fi = fd.LVSFICN(spot,volsdd_new,volsd_new,vols0_new,volsu_new,volsuu_new,[rd]*ntimes,[rf]*ntimes,break_times_new,alpha,beta,extrap_fact,nu,nt,nsd,texps[i])
                fi.go_forward(texps[i])
                prices = [fi.interp(strike) for strike in time_strikes]
                                
            model_vols = [bs.imp_vol(True,spot,strike,texps[i],rd,rf,price) for strike, price in zip(time_strikes,prices)]
            diffs      = [model_vol-imp_vol for model_vol, imp_vol in zip(model_vols,time_vols)]
            return diffs
        
        guess = time_vols
        fit = scipy.optimize.leastsq(arg_func,guess)[0]
        
        volsdd.append(fit[0])
        volsd.append(fit[1])
        vols0.append(fit[2])
        volsu.append(fit[3])
        volsuu.append(fit[4])
        
        break_times.append(texps[i])
    
    return volsdd,volsd,vols0,volsu,volsuu

def run_lvs():
    '''Runs the calibration of local vols and prices a knockout under the LVS model'''
    
    # define the knockout option we want to price
    
    is_call = True
    strike  = 1.03
    ko      = 0.95
    is_up   = False
    texp    = 1
    
    # define the market data we'll use as an input to calibrate against
    
    spot  = 1
    rd    = 0.0
    rf    = 0.0
    texps = [1/12.,0.25,0.5,0.75,1]
    atms  = [0.075,0.078,0.080,0.0805,0.082]
    rrs25 = [0.0025,0,-0.005,-0.01,-0.0125]
    rrs10 = [rr25*1.8 for rr25 in rrs25]
    bfs25 = [0.0025,0.0030,0.0032,0.0030,0.0030]
    bfs10 = [bf25*3 for bf25 in bfs25]
    
    # define the model and numerical parameters we'll use
    
    beta  = 1
    nu    = 500
    nt    = 150
    nsd   = 5
    
    extrap_fact = 3.
    
    alphas = [i*0.1 for i in range(11)]
    ko_prices, opt_prices = [], []
    
    for alpha in alphas:

        # calculate the strikes and implied vols for the benchmarks

        strikes, imp_vols = [], []

        for i in range(len(texps)):
            texp       = texps[i]
            atm_vol    = atms[i]
            vol_25c    = atm_vol+rrs25[i]/2.+bfs25[i]
            vol_25p    = atm_vol-rrs25[i]/2.+bfs25[i]
            vol_10c    = atm_vol+rrs10[i]/2.+bfs10[i]
            vol_10p    = atm_vol-rrs10[i]/2.+bfs10[i]

            atm_strike = spot*math.exp((rd-rf)*texp+atm_vol*atm_vol*texp/2.)
            strike_25c = spot*math.exp((rd-rf)*texp+vol_25c*vol_25c*texp/2.-vol_25c*math.sqrt(texp)*num.cnorminv(0.25*math.exp(rf*texp)))
            strike_25p = spot*math.exp((rd-rf)*texp+vol_25p*vol_25p*texp/2.+vol_25p*math.sqrt(texp)*num.cnorminv(0.25*math.exp(rf*texp)))
            strike_10c = spot*math.exp((rd-rf)*texp+vol_10c*vol_10c*texp/2.-vol_10c*math.sqrt(texp)*num.cnorminv(0.10*math.exp(rf*texp)))
            strike_10p = spot*math.exp((rd-rf)*texp+vol_10p*vol_10p*texp/2.+vol_10p*math.sqrt(texp)*num.cnorminv(0.10*math.exp(rf*texp)))

            strikes.append((strike_10p,strike_25p,atm_strike,strike_25c,strike_10c))
            imp_vols.append((vol_10p,vol_25p,atm_vol,vol_25c,vol_10c))
        
        # calibrate the local vols

        volsdd,volsd,vols0,volsu,volsuu = calibrated_local_vols(spot,rd,rf,texps,strikes,imp_vols,alpha,beta,extrap_fact,nu,nt,nsd)
        
        print('alpha =',alpha)
        for i in range(len(texps)):
            print(texps[i],volsdd[i],volsd[i],vols0[i],volsu[i],volsuu[i])

        # now price the knockout option

        ntimes = len(texps)
        bi = fd.LVSBICN(spot,volsdd,volsd,vols0,volsu,volsuu,[rd]*ntimes,[rf]*ntimes,texps,alpha,beta,extrap_fact,nu,nt,nsd)
        bi.add_knockout(ko,is_up)
        bi.initialize_payoff(payoff.OptionPayoff(is_call,strike),texps[i])
        bi.go_back(0)
        ko_price = bi.interp(spot)

        print('Knockout price (bp) =',ko_price/spot*1e4)
        
        # now price the vanilla
        
        bi = fd.LVSBICN(spot,volsdd,volsd,vols0,volsu,volsuu,[rd]*ntimes,[rf]*ntimes,texps,alpha,beta,extrap_fact,nu,nt,nsd)
        bi.initialize_payoff(payoff.OptionPayoff(is_call,strike),texps[i])
        bi.go_back(0)
        opt_price = bi.interp(spot)

        print('Vanilla price (bp) =',opt_price/spot*1e4)
        
        print()
        
        ko_prices.append(ko_price/spot*1e4)
        opt_prices.append(opt_price/spot*1e4)
    
    plot.plotxy(alphas,ko_prices)
    plot.plotxy(alphas,opt_prices)

def run_corr_gamma():
    '''Calculates correlation gamma across a range of strikes for a cross vanilla'''
    
    spot1 = spot2 = 1
    vol1  = vol2  = 0.1
    rho   = 0.25
    texp  = 0.5
    
    # figure out a reasonable range of cross strikes to use as the x-axis in the plot
    
    spotx = spot1/spot2
    volx  = math.sqrt(vol1*vol1+vol2*vol2-2*rho*vol1*vol2)
    
    strike_lo = spotx*math.exp(-3*volx*math.sqrt(texp))
    strike_hi = spotx*math.exp( 3*volx*math.sqrt(texp))
    
    nstrikes  = 50
    dstrike   = (strike_hi-strike_lo)/(nstrikes-1)
    
    strikes, gammas = [], []
    
    for i in range(nstrikes):
        strikex = strike_lo+i*dstrike
        
        gamma = cross_option_correlation_gamma(spot1,spot2,vol1,vol2,rho,strikex,texp)
        
        strikes.append(strikex)
        gammas.append(gamma)
    
    plot.plotxy(strikes,gammas)

def run_dual_digi():
    '''Calculates the price of a dual digital put over a range of correlation values'''
    
    is_call = True
    digi1   = 0.65
    digi2   = 0.30
    
    rho_min = -0.99999
    rho_max =  0.99999
    nrho    = 100
    drho    = (rho_max-rho_min)/(nrho-1)
    
    rhos, prices = [], []
    
    for i in range(nrho):
        rho = rho_min+i*drho
        
        rhos.append(rho)
        prices.append(dual_digital_price(is_call,digi1,digi2,rho))
    
    plot.plotxy(rhos,prices)
    
if __name__=="__main__":
    run_corr_gamma()
    #run_lvs()
