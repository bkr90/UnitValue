# -*- coding: utf-8 -*-
"""
BEATRICE ROBSON
testing k-means on Nigeria community data using item_cd 14: imported rice
"""
import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook


source = pd.read_excel("hh_14.xlsx", 
                       sheet_name="export",
                       usecols="A:D,M,O")


    

#manually count k
k=15 #9 for item_cd 14 rice

#number of observations
obs = source.shape[0]

'''
for i in range(0,10):
    print(source.loc[i]["price_per_unit"])
    
max(source["price_per_unit"])
'''


#restrict printing to 2 decimal points (global setting)
np.set_printoptions(precision=2, suppress=True)


#set range for initializing centroids
ub = source["price_per_unit"].values.max(0)
lb = source["price_per_unit"].values.min(0)

avg = sum(source["price_per_unit"].values)/obs
std = np.std(source["price_per_unit"].values)


#init centroid starting values
points = np.random.rand(k) * ub

print("points:\n", points)

#index to store results
index = np.zeros(obs)

#monitor stopping condition
stop = False
loop = 0
tolerance = .05
last = np.zeros(k)

while (stop == False):
    

    #iterate through price vector and find nearest centroid by percent distance
    for i in range(obs):
        #store distance to each centroid
        distance = np.zeros(k)
                
        #find distance to each centroid
        for n in range(0,k):
            distance[n] = abs( points[n] - source.loc[i]["price_per_unit"] ) / source.loc[i]["price_per_unit"]

        
        index[i] = np.argmin(distance)


    #find new centroid
    sums = np.zeros(k)
    counts = np.zeros(k)
    
    for i in range(0,obs):
        this = int(index[i])
        counts[this] += 1
        sums[this] += source.loc[i]["price_per_unit"]
        
    #calculate new center; if no thing ended up in that bucket, reset to 1
    for n in range(k):
        last[n] = points[n] #store copy to track stopping conditions
        
        if counts[n] > 0:
            points[n] = sums[n]/counts[n]
        else:
            points[n] = (np.random.rand(1) * 2 * avg )
    
    #print("new points:  ", points)
    #print("last is now: ", last)

    #calculate stopping condition
    stop = True
    for n in range(0,k):
        #print(counts[n], ": ", "change: ", (last[n] - points[n]) / points[n] , " point: ", points[n])
        if (abs(last[n] - points[n]) / points[n] ) > tolerance :
            stop = False
    
    loop += 1
    
    #safety
    if loop > 100 :
        stop = True
    
    print("\nloop: ", loop)
    
#print("counts: ", counts)
#print ("sums: " , sums)
#print("points: ", np.round(points,2))


print("loops: ", loop)
for n in range(0,k):
    print(counts[n], ": ", points[n])
          
          
          

        
#save to excel    
workbook_name = 'test.xlsx'
wb = load_workbook(workbook_name)
wb_indices = wb["indices_hh"]
wb_means = wb["points_hh"]


# New data to write:
wb_indices.append(list(index.flatten()))
wb_means.append(list(points.flatten()))



wb.save(filename=workbook_name)