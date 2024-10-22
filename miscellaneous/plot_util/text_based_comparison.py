import os
import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob
import itertools
import copy
import statistics
import sys
import re
import argparse
import matplotlib.pyplot as plt
import pandas as pd

def dataframe_to_table(df, ax):
# Convert DataFrame to table and add to plot (ax)
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    table.scale(1, 1.5)  # Optionally scale the table
    ax.axis('off')  # Turn off the axis for the table
    return table

def percentile_selection(row, df, column_key, percent):
    #set the column value to a var in order to use it to compare with others
    comparator = row[column_key] 
    percent_threshold = percent

    total_rows = len(df)
    total_hits = 0

    total_hits = ((df[column_key] > comparator) & (df['index'] == 0)).sum()
    num_rows_of_one_job = len(df[df['index'] == 1])

    #print(num_rows_of_one_job)
    #print(total_rows)

    #if (total_hits / (total_rows / (max(df['index'] + 1))* 100)) <= percent_threshold:
    if (total_hits / num_rows_of_one_job * 100) <= percent_threshold:
        #print(f"Total hits: {total_hits}, Number of rows: {total_rows}, top 10%, standard dev: {comparator}")
        return 1
    else:
        #print(f"Total hits: {total_hits}, Number of rows: {total_rows}, top 10%, standard dev: {comparator}")
        return 0

def calculate_mean(row, df, key):
    # Get the current row's Node Count and Job (Rank) Count
    node_count = row['Node Count']
    job_count = row['Job (Rank) count']
    index_value = row['index']

    # Filter the rows where 'Node Count' and 'Job (Rank) Count' match the current row,
    # but exclude rows where index is 0
    filtered_rows = df[(df['Node Count'] == node_count) &
                       (df['Job (Rank) count'] == job_count)]

    # Include the current row's 'iops' value
    key_sum = filtered_rows[key].sum()

    stdDev = np.std(filtered_rows[key])
    # Total number of rows involved (current row + filtered rows)
    total_rows = len(filtered_rows)
    mean = key_sum / total_rows

    # Calculate the mean performance
    return pd.Series([mean, stdDev])

def text_comparison (results_list, benchmark):
    #print(f"Length of list is {len(results_list[0])}")
    named_results = []

    for i in results_list:
        keys_counter = 0
        new_dict = {}
        for j in i:
            if benchmark == "fio":
                keys = ["node_list","bw_list","iops_list","processor_list","title"]
            elif benchmark == "ior":
                keys = ["node_list","bw_list","iops_list","processor_list","title"]
            #for k in j:
            #print(f"{k} is going into {keys[keys_counter]} list...")
            new_dict[keys[keys_counter]] = j 
            keys_counter += 1
            #print(k, "\n\n")
        named_results.append(new_dict)
    #print(named_results)
    #sys.exit()
    
    initial_node_list = named_results[0]['node_list']
    initial_processor_list = named_results[0]['processor_list']
    differences = 0

    for i in named_results:
        if i['node_list'] == initial_node_list:
            pass
        else:
            differences += 1

        if i['processor_list'] == initial_processor_list:
            pass
        else:
            differences += 2

        if differences == 1:
            print("node lists have differences, exiting...")
            sys.exit()
        elif differences == 2:
            print("processor lists have differences, exiting...")
            sys.exit()
        elif differences == 3:
            print("Both node lists and processor lists have differences, exiting...")
            sys.exit()
    '''
    bw_mean = {}
    iops_mean = {}

    #print(f"LENGTH OF NAMED RESULTS IS {len(named_results)}")
    for i in range(len(initial_node_list[0])):
        for j in range(len(initial_processor_list)):
            tmp_bw_mean = sum(d['bw_list'][i][j] for d in named_results if 'bw_list' in d) / len(named_results)
            bw_mean[f"nodes_{initial_node_list[0][i]}_procs_{initial_processor_list[j]}"] = tmp_bw_mean
            tmp_iops_mean = sum(d['iops_list'][i][j] for d in named_results if 'bw_list' in d) / len(named_results)
            iops_mean[f"nodes_{initial_node_list[0][i]}_procs_{initial_processor_list[j]}"] = tmp_iops_mean
    '''
    columns = ['Node count', 'Job (Rank) count', 'Performance', 'Mean performance', 'IOPS', 'Mean IOPS']

    new_list = []


    for i in named_results:
        for proc_index in range(len(i['processor_list'])):
            #for proc_index in range(len(i['node_list'][proc_index])):
            for node_count_index in range(len(i['node_list'][proc_index])):
                #print(f"{node_count_index}")
                #print(f"{i['node_list'][proc_index][node_count_index]}, {i['processor_list'][proc_index]}")
                new_dict = {}
                #print (f"Node count: {node_count_list[node_count_index]}, Job count: {i['processor_list'][node_count_index]}") 
                new_dict['Node Count'] = i['node_list'][proc_index][node_count_index]
                new_dict['Job (Rank) count'] = i['processor_list'][proc_index]
                new_dict['Performance (GB/s)'] = i['bw_list'][proc_index][node_count_index]
                #new_dict['Mean performance (GB/s)'] = bw_mean[f"nodes_{new_dict['Node Count']}_procs_{new_dict['Job (Rank) count']}"]
                new_dict['IOPS'] = i['iops_list'][proc_index][node_count_index]
                new_dict['title'] = i['title']
                #new_dict['Mean IOPS'] = iops_mean[f"nodes_{new_dict['Node Count']}_procs_{new_dict['Job (Rank) count']}"]
                new_dict['index'] = named_results.index(i)
                new_list.append(new_dict)

    '''
    for i in new_list:
        if i['Node Count'] == 4 and i['Job (Rank) count'] == 48:
            print(i,"\n")
    sys.exit()
    '''

    df = pd.DataFrame(new_list)
    #print(df)
    #sys.exit()
    #compare the element (for example, Perfromance (GB/s)) to the computed mean of that element (Mean performance (GB/s)) and isolate those data points which are in the top 10 percentile of all values sorted from highest removed from mean to lowest removed.
    df[['meanPerf', 'perfStdDev']] = df.apply(lambda row: calculate_mean(row, df,'Performance (GB/s)'), axis=1)
    df[['meanIOPS', 'iopsStdDev']] = df.apply(lambda row: calculate_mean(row, df,'IOPS'), axis=1)
    df['coefficient_of_variation'] =  df['perfStdDev'] / df['meanPerf'] * 100
    df['top10CoV'] = df.apply(lambda row: percentile_selection(row, df, 'coefficient_of_variation', 25), axis=1)
    
    pd.set_option('display.max_rows', None)  # Show all rows

    #---------------------Instead of doing all those row operations for 'top10CoV', I can sort the dataframe then take the highest 10% based on coefficient_of_variation
    top10df = df[(df['top10CoV'] == 1) & (df['index'] == 0)]
    sorted_top10df = top10df.sort_values(by='coefficient_of_variation')
    print(sorted_top10df[['Node Count','Job (Rank) count', 'Performance (GB/s)', 'coefficient_of_variation']])
    sorted_df = df.sort_values(by='coefficient_of_variation')
    #print(sorted_df)

    return df
