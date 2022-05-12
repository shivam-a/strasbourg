# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 16:40:52 2018

@author: slehmler
"""

import pandas as pd
import numpy as np

#https://stackoverflow.com/questions/39204595/deal-with-errors-in-parametrised-sigmoid-function-in-python
from scipy.special import expit

#takes production, attraction & distance/cost matrices
#and returns a list of trip-matrices (one for each activity type) 
def get_trip_matrices(P,A,C, betas = {"Work": 0.1, "School": 0.1, "University": 0.1, "Shopping": 0.1, "Leisure": 0.1, "Accompany": 0.1, "Other":0.1 }):
    #probably nicer/faster ways to do this, but for now:
    trip_dic = {}
    for activity in P:
        #scale A to the sum of P
        #generate trip matrix
        tm_df = _trip_matrix(P[activity],A[activity]*(P[activity].sum()/A[activity].sum()), C, betas[activity])
        #run ipf/furness/fratar on trip matrix
        trip_dic[activity] = _ipf(tm_df, P[activity],A[activity]*(P[activity].sum()/A[activity].sum()))
        #trip_dic[activity] = tm_df
    return trip_dic

def _trip_matrix(O,D,C, beta = 0.1):
    if O.size != D.size:
        raise ValueError("Production/Origin and Attraction/Destination Vectors are not the same size! \n {} != {}".format(O.size,D.size))
    elif not np.isclose(O.sum(),D.sum()):
        raise ValueError("Production and Atraction Vectors do not sum up to the same Value!\n {} != {}".format(O.sum(),D.sum()))
    else:
        cost = np.exp(-1*beta*C)
        #cost = cost.replace([np.inf, -np.inf], 0.1)
        #from JT's code:
        ## We zero all the cells that are in places were the cost is too high
        # This step is more useful for the calibr., but it can be used for ..
        # ..model application as well
        #....not doing this might be the reason for introducing Nan? Nope
        #max_cost = 120
        #a = (cost < max_cost).astype(int)
        #cost = a*cost
        cost.fillna(0, inplace =True)
        #print('cost *(O.sum()/sum(cost.sum(axis=0))) \n', cost *(O.sum()/sum(cost.sum(axis=0)))
        o= O.sum()
        sum_sum = cost.sum(axis=0)
        sum_c= sum(cost.sum(axis=0))
        ret= cost *(O.sum()/sum(cost.sum(axis=0)))
        return ret
    
#iterate proportional fittting
#also called furness, fratar...   
def _ipf(df, row, column):
    iterations = 0
    while True:
        iterations += 1
        start = df.copy()
        #fit for rows (production targets)
        df = df.divide(df.sum(axis=1), axis=0)
        df = df.fillna(0)
        df = df.mul(row, axis=0)

        #fit for columns (attraction targets)
        #df =df*column/df.sum(axis=0)
        df = df.divide(df.sum(axis=0), axis=1)
        df = df.fillna(0)
        #df = df.mul(column, axis=1)
        df = df.mul(column.reindex(df.index).values,axis=1)
        if start.subtract(df).abs().values.sum() < 0.0001 :
            break
        elif iterations > 1000:
            break
    return df
#    while True:
#        iterations += 1
#        start = df.copy()
#        #fit for rows (production targets)
#        with np.errstate(divide='raise'):
#            try:
#                row_factor = np.divide(row, df.sum(axis=1))
#            except FloatingPointError:
#                print('oh no!')
#        df = np.transpose(
#                        np.transpose(df)*np.transpose(row_factor)
#                        )
#        #fit for columns (attraction targets)
#        
#        #df =df*column/df.sum(axis=0)
#        #df = df.mul(column, axis=0)/df.sum(axis=0)
#        
#        #calculate fitting factor for attraction targets
#        #attr_factor = _factor(df.sum(axis=0), column)
#        column_factor = np.divide(column, df.sum(axis=0))
#        df = df.mul(column_factor, axis=0)
#        #df = df*column_factor
#        if start.subtract(df).abs().values.sum() < 0.0001 :
#            break
#        elif iterations > 100:
#            break
    return df

def find_beta(produ, attra, cost, cstar,
              coef=2., max_iterations=100,max_error=0.001):
    result_beta = 1000
    result_gap = 1000
    for randm in np.random.random_sample(100):
        coef = (10 + 10) * randm - 10
    # Initialize iterative procedure
        # Steps on page 192 of Modelling Transport
        # Step 1
        itera = 0  # 'm' in the book
        betazero = coef / cstar
        # Step 2
        # We apply a simple gravity with the chosen function, and a fratar
        synthmatrix = _trip_matrix(produ, attra, cost, betazero)
        synthmatrix =_ipf(synthmatrix,produ,attra)
        
        itera = itera + 1
        # We obtain the mean modelled trip cost czero ..
        czero = synthmatrix.mul(cost).values.sum()/synthmatrix.values.sum()
        # .. and estimate a better value for beta:
        betamminusone = betazero

        betam = betazero * czero / cstar

        # We compute the new matrix, cm and cmminusone
        synthmatrix = _trip_matrix(produ, attra, cost, betam)
        synthmatrix =_ipf(synthmatrix,produ,attra)
        
        cm = synthmatrix.mul(cost).values.sum()/synthmatrix.values.sum()
        cmminusone = czero

        # We compute the gap_beta between the new beta and the last one
        gap_beta = abs(1 - betam / betamminusone)
        gap_cstar = cm - cstar
        # Starts iterative process from step 3 onwards
        # while abs(gap_cstar > 1) and itera < max_iterations:
        while gap_beta > max_error and itera < max_iterations:
            itera = itera + 1

            aux = betam
            # Formula page 193
            betam = ((cstar-cmminusone)*betam -
                     (cstar-cm)*betamminusone) / (cm-cmminusone)
            betamminusone = aux

            # We compute the new matrix, cm and cmminusone
            synthmatrix = _trip_matrix(produ, attra, cost, betam)
            synthmatrix =_ipf(synthmatrix,produ,attra)
            cm = synthmatrix.mul(cost).values.sum()/synthmatrix.values.sum()
            cmminusone = cmminusone

            # We compute the gap_beta between the new beta and the last one
            gap_beta = abs(1 - betam / betamminusone)
            gap_cstar = cm - cstar
            if gap_cstar < result_gap:
                result_beta = betam
                result_gap = gap_cstar
    print("difference: {}".format(result_gap))
    return result_beta

def calibrate_beta(P,A,C,omtl):
    #minimize following function:
    #1. run gravity model
    #2. get mean trip length
    #3. calculate difference from observed mtl
    def to_minimize(beta, O,D,C, omtl):
        tm = _trip_matrix(O,D,C,beta)
        tm = _ipf(tm, O, D)
        
        mtl = tm.mul(C).values.sum()/tm.values.sum()
        #print("calculated trip length: {}, observed trip length: {}, difference: {}".format(mtl,omtl,mtl - omtl))
        return abs(mtl - omtl)
    initial_beta = 0.1
    beta_dic = {}

    from scipy.optimize import minimize
    #from Gravity import calibrate_gravity
    for activity in P:
        print('iterate activities', activity)
        #for initial_beta in np.arange(-10,10, 0.1):
        for rand in np.random.random_sample(50):
            initial_beta = (10 +10) * rand - 10
            current = minimize(to_minimize, initial_beta,  args=(P[activity], A[activity]*(P[activity].sum()/A[activity].sum()) , C, omtl[activity]), method= 'Nelder-Mead', options={ 'maxiter': 100} )
            if not "result" in locals():
                result = current
            if result.fun > current.fun:
                print(current)
                print(current.fun)
                result = current
        #beta = calibrate_gravity(P[activity].as_matrix(), A[activity]*(P[activity].sum()/A[activity].sum()), C.as_matrix(), omtl, "EXPO", coef=2.,verbose=True, max_iterations=100,max_error=0.001, max_cost=None, outmatrix=None)
        #print(beta)
        print(result)
        beta_dic[activity] = result.x
        #beta_dic[activity] = find_beta(P[activity], A[activity]*(P[activity].sum()/A[activity].sum()), C, omtl[activity])
    return beta_dic

if __name__ == "__main__":
#    O = pd.Series([5,10,15])
#    D = pd.Series([15,10,5])
#    C = pd.DataFrame([[2,2,2]]*3)

    A = pd.Series([35,40,25])
    P = pd.Series([20,30,35,15])
    C= pd.DataFrame([[6,6,3],[8,10,10],[9,10,9],[3,14,8]])
    
    A = pd.Series([0,400,500,802])
    P = pd.Series([400,200,400,702])
    #C is the cost-dataframe
    #each row i contains the cost to go from zone i to zone 1,2, ... j  
    C = pd.DataFrame([[3,11,18,22],
                      [12,3,12,19],
                      [15.5,13,5,7],
                      [24,18,8,5]])
    tm = _trip_matrix(P,A,C)
    tm= _ipf(tm,P,A)
    