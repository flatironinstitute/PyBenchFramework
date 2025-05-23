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

class ResultSet:
    def __init__(self, node_count, bw, iops, jobs_per_node):
        self.node_count = node_count
        self.bw = bw
        self.iops = iops
        self.jobs_per_node = jobs_per_node 
        # mean values
        self.mean_bw = 0
        self.mean_iops = 0
        #standard deviation from the mean
        self.relative_dev_bw = 0
        self.relative_dev_iops = 0
        #coefficient of variation
        self.CoV_bw = 0
        self.CoV_iops = 0 

    def __repr__(self):
        return f"ResultSet(node_count={self.node_count}, Bandwidth={self.bw}, IOPS={self.iops}, Jobs_per_node={self.jobs_per_node}, mean_bw={self.mean_bw}, relative_dev_bw={self.relative_dev_bw}, CoV_bw={self.CoV_bw}, mean_iops={self.mean_iops}, relative_dev_iops={self.relative_dev_iops}, CoV_iops={self.CoV_iops})"

    def eq (self, result_set):
        if self.node_count == result_set.node_count and self.jobs_per_node == result_set.jobs_per_node:
            return True
        else:
            return False

    def calc_relative_dev_and_CoV(self):
        self.relative_dev_bw = abs(self.bw - self.mean_bw) / self.mean_bw
        self.relative_dev_iops = abs(self.iops - self.mean_iops) / self.mean_iops

        #self.CoV_bw = (self.relative_dev_bw / self.mean_bw) * 100
        #self.CoV_iops = (self.relative_dev_iops / self.mean_iops) * 100

class JobResults:
    def __init__(self, title):
        self.result_set_list = []
        self.title = title
        unique_pairs = tuple()

    #Need to update this to read path directly from YAML file for newer jobs
    #broken code. Either fix or remove
    def get_job_IO_type(self):
        for text in ["read","write","randread","randwrite"]:
            print(self.title)
            if self.title[0] == f"* {text} *":
                pass
                #print (f"IOTYPE FOUND {text}")

    def append_partial_set (self, result_set: ResultSet):
        self.result_set_list.append(result_set)

    def __repr__(self):
        return f"JobResults(title={self.title}, result_set_list={self.result_set_list})"

    def check_value_and_order (self, job_results):
        for counter in range(len(self.result_set_list)):
            try:
                if self.result_set_list[counter].eq(job_results.result_set_list[counter]):
                    pass
                else:
                    return False
            except IndexError as e:
                print(f"Error in JobResults comparison. JobResult partial set lists are of unequal lengths. {e}")
    
        return True
    
    def find_unique_pairs(self):
        self.unique_pairs = {(getattr(obj, 'node_count', None), getattr(obj, 'jobs_per_node', None)) for obj in self.result_set_list}

def calc_mean (job_result_list):
    unique_pairs = job_result_list[0].unique_pairs
    for i in unique_pairs:
        total_bw = 0
        total_iops = 0
        average_bw = 0
        average_iops = 0
        divisor = len(job_result_list)

        node_count = i[0]
        jobs_per_node = i[1]
        
        for job in job_result_list:
            for result_set in job.result_set_list:
                total_bw += result_set.bw if result_set.node_count == node_count and result_set.jobs_per_node == jobs_per_node else 0 
                total_iops += result_set.iops if result_set.node_count == node_count and result_set.jobs_per_node == jobs_per_node else 0
        
        average_bw = total_bw / divisor
        average_iops = total_iops / divisor

        for job in job_result_list:
            for result_set in job.result_set_list:
                if result_set.node_count == node_count and result_set.jobs_per_node == jobs_per_node:
                    result_set.mean_bw = average_bw
                    result_set.mean_iops = average_iops

def new_text_comparison (results_list, benchmark):

    #print(results_list)
    named_results = []
    job_result_list = []
    job_counter = 0

    print("THIS IS FOR A ROW")
    print(results_list[0][4])
    #iterate over each job result set in the input row to this method. Each element is a result set from a benchmark job
    for i in results_list:
        job_result_list.append(JobResults(i[4]))
        #job_result_list[job_counter].get_job_IO_type()
        keys_counter = 0
        for j in range(len(i[0])):
            for k in range(len(i[0][j])):
                #integer / float / string (title)
                partial_result_set = ResultSet(i[0][j][k], i[1][j][k], i[2][j][k], i[3][j])
                job_result_list[job_counter].append_partial_set(partial_result_set)

        if job_counter >= 1:
            if job_result_list[job_counter].check_value_and_order(job_result_list[job_counter - 1]):
                pass
            else:
                print("Partial sets in Job result sets differ in either node_count or jobs_per_node")
                sys.exit()

        elif job_counter == 0:
            job_result_list[job_counter].find_unique_pairs()

        job_counter += 1

    calc_mean(job_result_list)


    counter = 0
    for i in job_result_list:
        print(f"Plot {counter}:")
        for j in i.result_set_list:
            j.calc_relative_dev_and_CoV()
            #print (j.node_count, j.jobs_per_node, j.bw, j.iops)
        result_set_list = i.result_set_list
        sorted_result_set_list = sorted(result_set_list, key=lambda result_set: result_set.relative_dev_bw, reverse=True)
        for j in range(2):
            print(f"node_count: {sorted_result_set_list[j].node_count}, job_per_node: {sorted_result_set_list[j].jobs_per_node}, percentage_deviation_from_mean={sorted_result_set_list[j].relative_dev_bw*100}, {sorted_result_set_list[j].bw}, {sorted_result_set_list[j].mean_bw}")
        average_dev = sum([result_set.relative_dev_bw*100 for result_set in result_set_list]) / len(result_set_list)
        print(f"Average data point percentage deviation from other plots: {average_dev}")
        print(f"Data point count: {len(i.result_set_list)}")
        print('')
        counter += 1

def text_comparison (results_list, benchmark):
    #print(f"Length of list is {len(results_list[0])}")
    named_results = []

    #iterate over each job result set in the input row to this method. Each element is a result set from a benchmark job
    for i in results_list:
        keys_counter = 0
        new_dict = {}
        #iterate over the lists in the job result set
        for j in i:
            if benchmark == "fio":
                keys = ["node_list","bw_list","iops_list","processor_list","title"]
            elif benchmark == "ior":
                keys = ["node_list","bw_list","iops_list","processor_list","title"]

            #for each key in "keys" list, create a key-value pair in the 'new_dict' temporary dictionary in which the key is the element in 'keys' (for example, 'node_list') and the value is the list extracted from the job result set (for the 'node_list' key, it would be the node list associated with the job result set)
            new_dict[keys[keys_counter]] = j
            keys_counter += 1

        #append each complete dict into the list. Maybe this could be a data frame instead of a list of dicts
        named_results.append(new_dict)
    #print(named_results)
    #sys.exit()
    
    initial_node_list = named_results[0]['node_list']
    initial_processor_list = named_results[0]['processor_list']
    differences = 0

    #Check that all the lists relevant for equivalent comparison are exactly the same, otherwise we can't compare results. This method is comparing result sets that should have the same number of nodes&job numbers per node (node list, job num list (proc list))
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
