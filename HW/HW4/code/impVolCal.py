"""
(c) 2015 Baruch College, MTH9865
Author: Zhenfeng Liang
Contact: Zhenfeng.Jose.Liang@gmail.com
Description: This is including functions to analyse the effect that imp correlation have on the cross volatility.
"""

import pandas as pd


class impVolCal:
    '''Implement main functionalities for HW4'''

    def __init__(self, data_path, S1, S2, Sx, product):
        '''
        data_path: the path to the data file
        S1, S2, Sx: the name of the USD pairs and cross pair
        product: boolean, if it is true, cross pair is the product of USD pairs, otherwise, ratio
        '''
        self.S1 = S1
        self.S2 = S2
        self.Sx = Sx
        self.product = product
        self.data = self.readData(data_path)
        self.corrMatr = self.calImpVolCorrMatr()

    def printStatistics(self, tenor, start_date, end_date):
        '''
        tenor: expiration tenor
        start_date, end_date: YYYY-MM-DD
        '''
        diff = self.calDiff(tenor, start_date, end_date)
        chg = self.calChange(tenor, start_date, end_date)

        print diff.describe()
        print chg.describe()


    def readData(self, data_path):
        xls_file = pd.ExcelFile(data_path)
        return xls_file.parse('Sheet1', index_col=0) # Get Date column as the index column


    # Vectorized
    def calImpVolCorrMatr(self):
        tmp1 = self.calImpVolCorr(self.data[self.S1 + " 1w"], self.data[self.S2 + " 1w"], self.data[self.Sx + " 1w"])
        tmp2 = self.calImpVolCorr(self.data[self.S1 + " 1m"], self.data[self.S2 + " 1m"], self.data[self.Sx + " 1m"])
        tmp3 = self.calImpVolCorr(self.data[self.S1 + " 6m"], self.data[self.S2 + " 6m"], self.data[self.Sx + " 6m"])
        tmp4 = self.calImpVolCorr(self.data[self.S1 + " 1y"], self.data[self.S2 + " 1y"], self.data[self.Sx + " 1y"])
        tmpMatr = pd.concat([tmp1, tmp2, tmp3, tmp4], axis=1)
        tmpMatr.columns = ['1w', '1m', '6m', '1y']

        return tmpMatr

    def calPrediction(self, tenor):
        S1_tenor = self.S1 + " " + tenor
        S2_tenor = self.S2 + " " + tenor
        predictMatr = self.predictCrossVol(self.data[S1_tenor], self.data[S2_tenor], self.corrMatr[tenor].shift(1))

        return predictMatr

    def calDiff(self, tenor, start_date, end_date):
        start = self.data.index.searchsorted(start_date)
        end = self.data.index.searchsorted(end_date)
  
        Sx_tenor = self.Sx + " " + tenor

        res = self.calPrediction(tenor).ix[start:end] - self.data.ix[start:end][Sx_tenor] 

        return res

    def calChange(self, tenor, start_date, end_date):
        start = self.data.index.searchsorted(start_date)
        end = self.data.index.searchsorted(end_date)

        Sx_tenor = self.Sx + " " + tenor

        res =  self.data.ix[start:end][Sx_tenor] - self.data.ix[start:end][Sx_tenor].shift(1) 

        return res

    def calImpVolCorr(self, sigma1, sigma2, sigmax):
        if self.product:
            return -1 * (sigma1 ** 2 + sigma2 ** 2 - sigmax ** 2) / (2 * sigma1 * sigma2) # Negative for product S1*S2
        else:
            return (sigma1 ** 2 + sigma2 ** 2 - sigmax ** 2) / (2 * sigma1 * sigma2) 
    

    def predictCrossVol(self, sigma1, sigma2, rho):
        if self.product:
            return (sigma1 ** 2 + sigma2 ** 2 + 2 * rho * sigma1 * sigma2) ** 0.5 # Plus sign for product S1*S2
        else:
            return (sigma1 ** 2 + sigma2 ** 2 - 2 * rho * sigma1 * sigma2) ** 0.5


        
