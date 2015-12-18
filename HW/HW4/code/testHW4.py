"""
(c) 2015 Baruch College, MTH9865
Author: Zhenfeng Liang
Contact: Zhenfeng.Jose.Liang@gmail.com
Description: This includes a test function for HW4
"""

from impVolCal import * 

def HW4Wrapper(data_path, S1, S2, Sx, tenor, product, start_date, end_date):

    ob = impVolCal(data_path, S1, S2, Sx, product)
    ob.printStatistics(tenor, start_date, end_date)
    

def testHW4():
    
    data_path = "fx_vol_data.xlsx"
    S1 = "AUDUSD"
    S2 = "USDJPY"
    Sx = "AUDJPY"
    product = True
    start_date = "2007-01-02"
    end_date = "2013-06-01"

    HW4Wrapper(data_path, S1, S2, Sx, '1w', product, start_date, end_date)
    HW4Wrapper(data_path, S1, S2, Sx, '1m', product, start_date, end_date)
    HW4Wrapper(data_path, S1, S2, Sx, '6m', product, start_date, end_date)
    HW4Wrapper(data_path, S1, S2, Sx, '1y', product, start_date, end_date)


if __name__ == '__main__':
    testHW4()
