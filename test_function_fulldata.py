# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 09:39:40 2024

@author: Beatrice Robson

UNIT VALUE PROJECT
Flow:
    1. cluster household observations using k-means
    2. determine unit-cluster frequencies
    3. approve community observations based upon hh unit-cluster frequencies
"""
####################################################################################
import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
import statistics

#restrict printing to 2 decimal points (global setting)
np.set_printoptions(precision=2, suppress=True)

#set k 
k=15

####################################################################################


#import all data
df_hh = pd.read_excel("kmeans_hh.xlsx", 
                       sheet_name = "export",
                       usecols="J:L")

df_com = pd.read_excel("kmeans_com_full.xlsx", 
                       sheet_name = "export",
                       usecols="A:O")

df_items = pd.read_excel("codes.xlsx", 
                       sheet_name = "item_codes",
                       usecols="A")


master_hh = df_hh.to_numpy()

#add a column of 0s to the community data; change to 1 if approved
master_com = df_com.to_numpy()
master_com = np.append(master_com, np.zeros(( master_com.shape[0]  ,1)), axis=1)

item_codes = df_items.to_numpy()


#where to save
save_as = "kmeans_outfile_5.xlsx"
outfile = load_workbook(save_as)
save_data = outfile["data"]
save_clusters = outfile["clusters"]



####################################################################################
#Takes in an array (should be restricted to one item_cd) and k=clusters, and returns
#an array of clusters, and original array with indices appended to each row 
####################################################################################
def kmeans(this_hh, k):
        
    #item_cd = this_hh[0,1]
    
    #print("k: ", k, ", item_cd: ", item_cd)
    
    #create col to store indices
    this_hh = np.append(this_hh, np.zeros(( this_hh.shape[0]  ,1)), axis=1)    
    
    #array shape#########################################
    #[unit_cd][item_cd][price_per_unit][index]
    
    obs = this_hh.shape[0]
    
    #set range for initializing centroids
    ub = this_hh[:,2].max()
    lb = this_hh[:,2].min()
    
    avg = sum(this_hh[:,2]) / obs
    median = statistics.median(this_hh[:,2])
    std = np.std(this_hh[:,2])
        
    #create array to store clusters; [centroid][index][count][max][min][item_cd]
    clusters = np.zeros((k,6))
    
    for i in range(k):
        clusters[i][0] = np.random.rand() * ub
        clusters[i][1] = i
        clusters[i][5] = this_hh[0,1]
          
    #print(clusters)
    
    #monitor stopping condition
    stop = False
    loop = 0
    tolerance = .05
    prev = np.zeros(k)

    while (stop == False):
        
        
        #iterate through price vector and find nearest centroid by percent distance#####
        for i in range(obs):
            #store distance to each centroid
            distance = np.zeros(k)
                    
            #find distance to each centroid
            for j in range(0,k):
                distance[j] = abs( clusters[j,0] - this_hh[i,2] ) / this_hh[i,2]
    
            this_hh[i,3] = np.argmin(distance) #index of the lowest distance
    
    
        #find new centroid#############################################################
        sums = np.zeros(k)
        
        for i in range(k):
            clusters[i,2] = 0
        
        #find the sum and counts in each cluster to calculate average
        for i in range(0,obs):
            this = int(this_hh[i,3])
            clusters[this,2] += 1
            sums[this] += this_hh[i,2]
            
        #calculate new center; if no thing ended up in that bucket, reset to 1#######
        for i in range(k):
            prev[i] = clusters[i,0] #store copy to track stopping conditions
            
            #if cluster is populated, new center is average of all its prices
            if clusters[i,2] > 0:
                clusters[i,0] = sums[i]/clusters[i,2]
            else:
                clusters[i,0] = (np.random.rand(1) * 2 * median ) #else create new centroid
        
        #calculate stopping condition################################################
        stop = True
        for n in range(0,k):
            if (abs(prev[n] - clusters[n,0]) / clusters[n,0] ) > tolerance :
                stop = False
        
        loop += 1
        
        #safety#########
        if loop > 100 :
            stop = True
        
        #print(" loop: ", loop)
        #print(clusters)
        
    #print("Item code ", item_cd, " converged in ", loop, " iterations.")
    #print("clusters:\n", clusters)

    
    
    #determine upper and lower bound for clusters####################################
    for point in range(0,k):
        
        #subset hh data into this cluster only
        this_cluster = np.zeros((1,4))
        
        for j in range( this_hh.shape[0] ):
            if(this_hh[j,3] == point):
                this_cluster = np.vstack([this_cluster, this_hh[j,:]])
        #delete leading row of 0s
        if(this_cluster.shape[0] > 1 ):
            this_cluster = np.delete(this_cluster, (0), axis=0)
        else:
            print("safety check: item ", this_hh[0,1])
        
        #print("this cluster: ", k, "\n", this_cluster)
        
        #identify max and min of this cluster
        clusters[point,3] = this_cluster[:,2].max()
        clusters[point,4] = this_cluster[:,2].min()
    
    #print("ending with:\n" , clusters)

    output = [clusters, this_hh]
    return output
        



##########################################################################################
#Takes an array of indexed observations and determines the number of times each unit appears 
#in each cluster. Returns an array where rows are item numbers and columns are clusters,
#and contents are percent of that unit appearing in that cluster
##########################################################################################
def cluster_freq(this_hh):
    
    #list units reported in this item, and count of each unit#############################
    unit_codes, unit_count = np.unique(this_hh[:,0], return_counts=True)
    
    n_units = unit_codes.shape[0]
    
    #put em in a nice array for safekeeping
    unit_list = np.zeros(( n_units ,2))
    unit_list[:,0] = unit_codes
    unit_list[:,1] = unit_count #   :)
    
    #each row represents one unit, each column shares an index with a cluster############
    #so entry [0,3] will be the percent of observations of unit 0 in cluster 3
    freq_table = np.zeros(( n_units , k ))
    
    
    #do for each unit###################################################################
    for i in range( n_units ):
        
        #subsample to just a single unit
        this_unit = np.zeros( this_hh.shape[1] )
        
        for j in range(  this_hh.shape[0] ):
            if (this_hh[j,0] == unit_list[i,0]):
                this_unit = np.vstack([this_unit, this_hh[j,:] ])
        this_unit = np.delete(this_unit, (0), axis=0)
                
        #print("this unit: \n", this_unit)
        
        #find times each cluster occurs for this particular unit
        cluster_index, cluster_count = np.unique(this_unit[:,3], return_counts=True)
        n_clusters = cluster_index.shape[0]
        
        #determine percent of this unit's instances are observed in each cluster############
        for j in range(n_clusters):
            cluster_no = int( cluster_index[j] )
            freq_table[i, cluster_no] = cluster_count[j] / unit_count[i]
            

    return freq_table


        

    

##########################################################################################
#Takes the freq table and retuns the clusters that represent the 80% most reported clusters
#for input unit 
##########################################################################################
def top_clusters(freq_table, unit):
    
    #identify most representative cluster for this unit. Store its index and frequency
    c_list = np.zeros((1,2))
    c_list[0,0] = np.argmax( freq_table[unit,:] )
    c_list[0,1] = np.max(    freq_table[unit,:] )
    #print("before" , c_list)
    freq_table[ unit, int( c_list[0,0] ) ] = 0
    
    #print("after", c_list)
    total_represented = c_list[0,1]
    
    #print("first cluster for unit ", unit, " : ", total_represented)
    
    #run until we have at least of 80% of the observations accounted for
    while (total_represented < 0.8):
        c_temp = np.zeros((1,2))
        c_temp[0,0] = np.argmax( freq_table[unit,:] )
        c_temp[0,1] = np.max(    freq_table[unit,:] )
        freq_table[ unit, int( c_temp[0,0] ) ] = 0
        
        c_list = np.vstack( [ c_list, c_temp ] )
        
        total_represented += c_temp[0,1]
        #print("rep: ", total_represented)
        
    #print("unit row: ", unit, "list: \n", c_list)

    return c_list





##########################################################################################
#marks community observations of this item_cd as "approved" if it falls within a 
#unit-cluster containing a significant portion of the hh observations
##########################################################################################
def approve_com(freq_table, community, this_hh, clusters):
    
    unit_codes, unit_count = np.unique(this_hh[:,0], return_counts=True)
    n_units = freq_table.shape[0]
    
    obs_com = community.shape[0]

    #loop for each unit this item_cd has observations of
    for i in range(n_units):
        this_unit = unit_codes[i]
        this_item = this_hh[0,1]
        
        #determines most representative clusters
        c_list = top_clusters(freq_table, i)
        n_clusters = c_list.shape[0]
        
        #iterate down all community observations
        for j in range(obs_com):
            
            com_unit = community[j,9]
            com_item = community[j,10]
            com_price = community[j,11]
            
            #set approve to true, then run through all conditions
            approve = True;
            
            #is this item correct?
            if ( com_item != this_item):
                approve = False            
            
            #is this unit correct?
            if ( com_unit != this_unit ):
                approve = False
            
            #iterate over all approved clusters for unit i
            cluster_match = False
            for l in range( n_clusters ):
                this_cluster = int( c_list[l,0] )
                this_ub = clusters[this_cluster, 3]
                this_lb = clusters[this_cluster, 4]
                if( this_lb < com_price and this_ub > com_price ):
                    #print(com_price, clusters[this_cluster,0])
                    cluster_match = True
                    
            #does price fall within range of one of our approved clusters?
            if (cluster_match == False):
                approve = False

            #if still true, obs is approved
            if(approve == True):
                community[j,15] = 1
                
    return community



##########################################################################################
##########################################################################################
#                                    begin main
##########################################################################################
##########################################################################################
#this will be a loop through the item_cd values we want; will pull all item_cd present in EASI model
for m in range ( len(item_codes) ):
    
    
    j = int( item_codes[ m ])
    #j = 14 #temp hard code to specific value
    print("iteation ", m, ", item_cd " , j)
    
    
    #subset data to item code i#########################################################
    obs_hh = master_hh.shape[0]
    
    #create subsample using only the item code we want
    this_hh = np.zeros((1,3))
    for m in range( obs_hh):
        if (master_hh[m][1] == j):
            this_hh = np.vstack([this_hh, master_hh[m,:] ])
    #remove leading row of 0s
    this_hh = np.delete(this_hh, (0), axis=0)
    
    
    #cluster hh data ###################################################################
    results = kmeans(this_hh, k)  
    
    clusters = results[0]
    this_hh = results[1]
    
    #print(clusters)

    
    #determine cluster representation for each unit######################################
    freq_table = cluster_freq(this_hh)
    
    
    #approve community observations #####################################################
    cleaned_com = approve_com(freq_table, master_com, this_hh, clusters)
    
    for i in range( k ):
        save_clusters.append(list(clusters[i,:].flatten()))
     
    
labels = ["phase", "zone", "state", "lga", "sector", "ea", "available", "price", "qty", "unit_cd", "item_cd", "price_per_unit", "conv_factor", "price_per_kg", "unit_desc", "keep" ]
    
save_data.append(labels)

for i in range( cleaned_com.shape[0]):
    save_data.append(list(cleaned_com[i,:].flatten()))
        
outfile.save(filename = save_as)
    