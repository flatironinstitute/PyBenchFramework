import glob
import sys, os
import json
import matplotlib.pyplot as plt
import pandas as pd
import math, statistics
from matplotlib.ticker import MultipleLocator
import re
from plot_util.text_based_comparison import text_comparison, dataframe_to_table
import numpy as np

def plot_serverless_FIO(directory, title, block_size, optional_plot_block_size=None):
    
    # Find all files matching the pattern "combined*.json"
    file_pattern = f"{directory}/combined*{block_size}.json"
    files = glob.glob(file_pattern)

    # Dictionary to store parsed data
    data = {}

    # Parse each JSON file and store the data
    for file_el in files:
        tmplist = []
        try:
            with open(file_el, 'r') as f:
                content = json.load(f)
                nodes = content["nodes"]
                int_nodes = int(content["nodes"])
                processors = content["processors"]
                bw = content["bw"]
                iops = content["iops"]
                tmplist.append(int_nodes)
                tmplist.append(processors)
                tmplist.append(bw)
                tmplist.append(iops)

                # Ensure the key exists in the dictionary
                if processors not in data:
                    data[processors] = []
                data[processors].append(tmplist)
        except FileNotFoundError:
            print(f"The file {file_el} was not found.")

    sorted_data = {k: v for k, v in sorted(data.items(), key=lambda item: item[0])}
    for key in sorted_data:
        sorted_data[key] = sorted(sorted_data[key], key=lambda x: x[0])


    #from collections import OrderedDict
    nodes = []
    bws = []
    iops = []
    processors = []

    nodes_list = []
    bw_list = []
    iops_list = []
    processor_counts = []

    for key in sorted_data:
    
        for value in sorted_data[key]:
            nodes.append(value[0])
            if optional_plot_block_size is None:
                bws.append(value[2]/1e6)
            elif optional_plot_block_size == "1M":
                bws.append(value[2]/1e3)
            iops.append(value[3])
        
        nodes_list.append(nodes)
        bw_list.append(bws)
        iops_list.append(iops)
        processor_counts.append(key)
    
        nodes = []
        bws = []
        iops = []

    # Plotting the data
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    # Plot Total bw and Total iops
    for i in range(len(nodes_list)):
        ax1.plot(nodes_list[i], bw_list[i], '-', label=f'{processor_counts[i]}_jobs')
        ax2.plot(nodes_list[i], iops_list[i], 'o', label=f'{processor_counts[i]}_jobs')

    ax2.set_ylabel("IOPS")
    ax1.set_xlabel('Node count')
    if optional_plot_block_size == "1M":
        ax1.set_ylabel('MB/s')
    else:
        ax1.set_ylabel('GB/s')
    ax1.set_title(title)
    ax1.legend(title='Type of run')
    plt.xticks(rotation=45)
    plt.tight_layout()
    # Set x-axis ticks to increment by 2
    plt.xticks(range(0, max(nodes_list[0])+1, 2))
    #plt.show()
    
    return fig, ax1, ax2

def return_FIO_data(directory, title, block_size, optional_plot_block_size=None):
    
    # Find all files matching the pattern "combined*.json"
    upper_block_size = block_size.upper()
    lower_block_size = block_size.lower()

    file_pattern = f"{directory}/combined*{upper_block_size}*"
    files = glob.glob(file_pattern)
    if not files:
        file_pattern = f"{directory}/combined*{lower_block_size}*"
        files = glob.glob(file_pattern)

    # Dictionary to store parsed data
    data = {}
    if not files:
        print(f"The file pattern {file_pattern} did not yield any results.")
        return 0

    # Parse each JSON file and store the data
    for file_el in files:
        tmplist = []
        try:
            with open(file_el, 'r') as f:
                content = json.load(f)
                #if content == dict:
                nodes = content["nodes"]
                int_nodes = int(content["nodes"])
                processors = content["processors"]
                if "bw" in content:
                    bw = content["bw"]/1e6
                    for key, value in content['node_list'].items():
                        tmp_item_bw = value['node_bw']/1e6
                        value['node_bw'] = tmp_item_bw

                elif content["mbw"]:
                    bw = content["mbw"]/1e3
                    for key, value in content['node_list'].items():
                        tmp_item_bw = value['node_bw']/1e3
                        value['node_bw'] = tmp_item_bw

                iops = content["iops"]
                tmplist.append(int_nodes)
                tmplist.append(processors)
                tmplist.append(bw)
                tmplist.append(iops)
                tmplist.append(content['node_list'])
                # Ensure the key exists in the dictionary
                if processors not in data:
                    data[processors] = []
                #print(tmplist)
                data[processors].append(tmplist)
        except FileNotFoundError:
            print(f"The file {file_el} was not found.")

    sorted_data = {k: v for k, v in sorted(data.items(), key=lambda item: item[0])}
    for key in sorted_data:
        sorted_data[key] = sorted(sorted_data[key], key=lambda x: x[0])

    #from collections import OrderedDict
    nodes = []
    node_count = []
    bws = []
    iops = []
    processors = []

    node_count_list = []
    bw_list = []
    iops_list = []
    processor_counts = []
    node_list = []
    for key in sorted_data:
    
        for value in sorted_data[key]:
            node_count.append(value[0])
            bws.append(value[2])
            iops.append(value[3])
            nodes.append(value[4])
        
        node_count_list.append(node_count)
        bw_list.append(bws)
        iops_list.append(iops)
        processor_counts.append(key)
        node_list.append(nodes)
    
        node_count = []
        bws = []
        iops = []
        nodes = []
    return node_count_list, bw_list, iops_list, processor_counts, node_list

def mod_return_FIO_data(directory, title, block_size, benchmark, optional_plot_block_size=None):
    plot_title = []
    tmp_title = ''

    #identifier = re.split('/', directory)[2]
    #print(benchmark)
    if benchmark.upper() == "IOR" or benchmark.lower() == "ior":
        identifier = re.split('/', directory)[3]
        node_count_list, bw_list, iops_list, processor_counts, node_list = return_FIO_data(directory, title, block_size, "1M")
    else:
        node_count_list, bw_list, iops_list, processor_counts, node_list = return_FIO_data(directory, title, block_size)

    try:
        with open (f"{directory}/job_note.txt", 'r') as file:
            for line in file:
                if "PLOT TITLE" in line.upper() or "plot title" in line.lower():
                    tmp_title = re.split(':', line)[1]
                    plot_title.append(f"{tmp_title}")
            if tmp_title == '':
                print(f"Plot title not found for directory: {directory}")
                plot_title.append(f"Title not found")
    except FileNotFoundError:
        print(f"File {directory}/job_note.txt not found.")
        plot_title.append("Title not found")
    
    return node_count_list, bw_list, iops_list, processor_counts, plot_title, node_list 

def plot_and_compare_mdtest(result_list, output_path):
    #print(result_list)
    #print(output_path)
    #sys.exit()
    #num_plots = len(result_list)
    #print(result_list)
    num_plots = len(result_list) * 6#7 
    num_plot_cols = len(result_list)
    #print(num_plots)
    #print(len(result_list))
    #print(result_list['title'])
    
    num_plot_rows = 1
    if num_plots > num_plot_cols:
        remainder = num_plots % num_plot_cols
        if remainder == 0:
            num_plot_rows = int(num_plots / num_plot_cols)
        else:
            num_plot_rows = int(num_plots // num_plot_cols + 1)
    
    fig, axs = plt.subplots(num_plot_rows, num_plot_cols, figsize=(5 * num_plot_cols, 5 * num_plot_rows))
    #fig, axs = plt.subplots(num_plot_rows, num_plot_cols, figsize=(6 * num_plot_cols, 6 * num_plot_rows))
   
    if num_plots == 1:
        axs = [axs]  # Ensure axs is a list with one element
    elif num_plot_rows > 1 or num_plot_cols > 1:
        axs = axs.flatten()  # Flatten the 2D array into a 1D array for easy indexing

    filename = ""

    key_list = ["Directory creation",
            "Directory stat",
            "Directory removal",
            "File creation",
            "File stat",
            #"File read",
            "File removal"
            #"Tree creation",
            #"Tree removal"
            ]
    plot_counter = 0
    
    # Set the column titles
    for col in range(num_plot_cols):
        x_position = (col + 0.5) / num_plot_cols
        fig.text(x_position,0.97, f'{result_list[col][0].iloc[0]["plot_title"]}', ha='center', va='bottom', fontsize=16)
        filename = result_list[col][0].iloc[0]["plot_title"]

    for op_index in range(len(key_list)):

        max_perf = 0
        is_max_here = 0
        for idx,file_lists in enumerate(result_list):
            #print(result_list)
            #break
            ax = axs[plot_counter]

            all_dict = {}

            for dataframe in file_lists:
                #print(dataframe)
                tmp_list = []
                node_list = []
                ranks_per_node_list = []
                mean_performance_list = []

                node_count = int(dataframe.loc[dataframe['operation'] == key_list[op_index], 'node_count'].values[0])

                #if key_list[op_index] != "File read" and key_list[op_index] != "File stat" and key_list[op_index] != "Directory stat" and key_list[op_index] != "File removal" or node_count > 2:
                ranks_per_node = int(dataframe.loc[dataframe['operation'] == key_list[op_index], 'ranks_per_node'].values[0])
                files_per_rank = float(dataframe.loc[dataframe['operation'] == key_list[op_index], 'files_per_rank'].values[0])
                mean_performance = float(dataframe.loc[dataframe['operation'] == key_list[op_index], 'Mean'].values[0])
                tmp_list.append(node_count)
                tmp_list.append(ranks_per_node)
                tmp_list.append(mean_performance)
                tmp_list.append(files_per_rank)

                if ranks_per_node not in all_dict:
                    all_dict[ranks_per_node] = []
                all_dict[ranks_per_node].append(tmp_list)

            sorted_data = {k: v for k, v in sorted(all_dict.items(), key=lambda item: item[0])}
            for key in sorted_data:
                sorted_data[key] = sorted(sorted_data[key], key=lambda x: x[0])

            nodes = []
            mean_perf = []
            files_per_rank = []
            ranks_per_node = []

            nodes_list = []
            mean_perf_list = []
            files_per_rank_list = []
            ranks_per_node_counts = []

            for key in sorted_data:

                for value in sorted_data[key]:
                    nodes.append(value[0])
                    mean_perf.append(value[2])
                    files_per_rank.append(value[3])

                nodes_list.append(nodes)
                mean_perf_list.append(mean_perf)
                files_per_rank_list.append(files_per_rank)
                ranks_per_node_counts.append(key)

                nodes = []
                mean_perf = []
                files_per_rank = [] 
            
            for i in range(len(nodes_list)):
                ax.plot(nodes_list[i], mean_perf_list[i], '-o', label=f'{ranks_per_node_counts[i]} ranks')

            #print(mean_perf_list)
            ax.xaxis.set_major_locator(MultipleLocator(2))
            ax.set_xlabel('nodes')
            ax.set_ylabel('OPS/sec')
            ax.set_title(key_list[op_index])

                #max_y = 0
                #print(mean_perf_list[plot_counter])
            for perf_list in mean_perf_list:
                if max_perf <= max(perf_list):
                    max_perf = max(perf_list)
                    is_max_here = plot_counter
                    #print(f"max is in plot {is_max_here}")
                    ax.set_ylim(0, max_perf * 1.1)

                
            #print(f"Column num is {num_plot_cols}, and current plot is {plot_counter}")
            if (plot_counter + 1) % num_plot_cols == 0 and plot_counter > 1:
                print(f"Last plot in row!")
                #print(f"Column num is {num_plot_cols}, and current plot is {plot_counter}")
                #start_of_loop = plot_counter - (num_plot_cols - 1)
                #end_of_loop = plot_counter
                #print(f"Start of loop is {start_of_loop}, and end of loop is {end_of_loop}")
                for i in range (plot_counter - (num_plot_cols - 1), plot_counter + 1):
                    #print(f"counter is {i}, and max is in plot {is_max_here}")
                    if i != is_max_here:
                        axs[i].sharey(axs[is_max_here])
                        print(f"Plot {i} sharing the axis of plot {is_max_here}!")
                max_perf = 0

            #ax.set_ylim(bottom=0)
            ax.legend(title='Ranks per node')
            plot_counter += 1
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust layout to make room for column titles

    filename = filename.lstrip()
    filename = filename.rstrip()
    filename = re.sub(',', '', filename)
    filename = re.sub('\n', '_', filename)
    final_filename = re.sub(' ', '_', filename) 
    print(final_filename)
    #final_filename = re.sub(r'[^A-Za-z0-9._-]+', '', 'test_mdtest_dir_plotting')

    plt.savefig(f"{output_path}/{final_filename}.svg", format="svg")
    

def plot_and_compare(all_result_list, output_path, list_of_lists):
    #Do I need lists or dicts of lists
    #How about two dicts that each have lists as values for each key?
    #Each of these 'all_result_list' elements is a list containing values for each job result set to be plotted. Each job result set is further broken down into nested lists. We get the length of this 'all_result_list' in order to know how many job result sets we're plotting in this call of 'plot_and_compare'

    num_plots = len(all_result_list)  # Determine the number of plots needed
    #print(num_plots)
    #num_rows = 2
    fig, axs = plt.subplots(1, num_plots, figsize=(10 * num_plots, 9), sharey=True)

    if num_plots == 1:
        axs = [axs]  # Ensure axs is a list with one element
    elif num_plots > 1:
        axs = axs.flatten()  # Flatten the 2D array into a 1D array for easy indexing

    filename = []
    #print(len(all_result_list))
    #print(all_result_list)

    iop_min = 0 #min(iop_list[i])
    iop_max = 0 #max(iop_list[i])
    bw_min = 0
    bw_max = 0
    lim_counter = 0
    bw_lim_counter = 0
    
    for lists in all_result_list:
        node_count_list, bw_list, iop_list, proc_list, plot_title, node_list = lists
        for list_el in iop_list:
            if lim_counter == 0:
                iop_min = min(list_el)
                iop_max = max(list_el)
            else:
                if iop_min >= min(list_el):
                    iop_min = min(list_el)
                if iop_max <= max(list_el):
                    iop_max = max(list_el)
            lim_counter += 1
        
        for list_el in bw_list:
            if bw_lim_counter == 0:
                bw_min = min(list_el)
                bw_max = max(list_el)
            else:
                if bw_min >= min(list_el):
                    bw_min = min(list_el)
                if bw_max <= max(list_el):
                    bw_max = max(list_el)
            bw_lim_counter += 1
    
    iop_min *=0.9
    iop_max *=1.1
    bw_min *=0.9
    bw_max *=1.1
    metrics = {}

    #print(f"LIMITS ARE: BW {bw_min},{bw_max} and IOPS {iop_min},{iop_max}")
    for idx, lists in enumerate(all_result_list):
    
        metrics[f"{idx}"] = []
        metrics_counter = 0

        node_count_list, bw_list, iop_list, proc_list, plot_title, node_list = lists
        
        #print (node_count_list) #bw_list, iop_list, proc_list, plot_title, node_list)
        def find_stdev_from_nodelist(node_dict):
            value_list = []
            #print("HELLO")
            for key, value in node_dict.items():
                value_list.append(value['node_bw'])
                #print(value['node_bw'])

            node_perf_stdev = statistics.stdev(value_list)
            #error_metric = node_perf_stdev * math.sqrt(len(value_list))
            error_metric = node_perf_stdev * len(value_list)
            return error_metric

        #print(node_list)

        # Calculate the row and column indices for the current subplot
        #if num_rows != 1:
        ax = axs[idx]
        #if idx == 0:
        ax2 = ax.twinx()
        ax2.set_ylabel("IOPS")
        max_error = 0


        #ax.set_units()
        for i in range(len(node_count_list)):
            errorlist = np.zeros((2, len(node_count_list[i])))  # Shape (2, N)

            for j in range(len(node_count_list[i])):
                
                # Store errors in errorlist (2, N)
                #print(node_list[i][j])
                if len(node_list[i][j]) > 1:
                    error = find_stdev_from_nodelist(node_list[i][j])
                else:
                    error = 0.0
                errorlist[0, j] = error  # Lower error (row index 0)
                errorlist[1, j] = error  # Upper error (row index 1)
                
                # Add error bar metric to list here. How to structure list? let's try json. Add plot count to the error metric (e.g. metrics could be a dict the keys of which are the plot counters and the values of which are lists of dicts where the keys are 'node count', 'proc count', and 'error metric', and the values correspond to each.            
                tmpdict = {}
                metrics[f"{idx}"].append(tmpdict)
                metrics[f"{idx}"][metrics_counter]['node count'] = node_count_list[i][j]
                metrics[f"{idx}"][metrics_counter]['proc count'] = proc_list[i]
                metrics[f"{idx}"][metrics_counter]['error percentage'] = int(error / bw_list[i][j] * 100)
                metrics_counter += 1

            # Plot with error bars
            ax.errorbar(
                    node_count_list[i],
                    bw_list[i],
                    yerr=errorlist,
                    fmt='o-',
                    capsize=5,
                    label=f'{proc_list[i]}_jobs'
                    )
            if max(errorlist[1]) >= max_error:
                max_error = max(errorlist[1])
            
        ax2.set_ylim(0, iop_max)
        if max_error > 0 :
            ax.set_ylim(0, max_error + bw_max)
            print(max_error/bw_max)
        else:
            ax.set_ylim(0, bw_max)

        plot_title[0] = plot_title[0].replace("\n", "")
        ax.xaxis.set_major_locator(MultipleLocator(2))
        ax.set_xlabel('nodes')
        ax.set_ylabel('GB/s')
        ax.set_title(plot_title[0])
        ax.legend(title='Type of run')
        ax.tick_params(direction='out', labelleft=True) 
        if idx <= 1:
            filename.append(re.split('-',plot_title[0].strip(" "))[0])
        
    final_filename = "_".join(filename)
    final_filename = final_filename.replace(" ", "_")
    final_filename = final_filename.replace("\n", "")
    final_filename = re.sub(r'[^A-Za-z0-9._-]+', '', final_filename)
    print(final_filename)
    #return text from text comparison methods. Return outliers (highest differences between datapoints) in a table? And add some commentary...
    
    # Add some global text (outside the plot area)
    #fig.text(0.5, 0.1, 'This is some text below the plot', ha='center', fontsize=12)
    
    #final_filename = "testing_fio_ior_compare"
    with open (f"{output_path}/metrics.json", 'w') as f:
        json.dump(metrics, f, indent=4)
    plt.savefig(f"{output_path}/{final_filename}.svg", format="svg")
    plt.close()

def convert_mdtest_data_in_parts(job_directory):
    key_list = {"Directory creation",
            "Directory stat",
            "Directory removal",
            "File creation",
            "File stat",
            "File read",
            "File removal",
            "Tree creation",
            "Tree removal",
            "Operation"
            }
    values = ["Operation",
            "Max",
            "Min",
            "Mean",
            "Std Dev"
            ]
    
    if not os.path.exists(f"{job_directory}/json_output"):
        os.makedirs(f"{job_directory}/json_output")

    file_pattern = f"{job_directory}/mdtest*YuC*ranks*"
    files = glob.glob(file_pattern)

    for i in files:
        file_name_dict = {}
        file_name_dict["create"] = re.split('/',i)[len(re.split('/',i)) - 1]
        file_name_dict["stat"] = file_name_dict["create"].replace("YuC", "YuT")
        file_name_dict["remove"] = file_name_dict["create"].replace("YuC", "Yur")
        #print(file_name_dict)
        #sys.exit()
        tmp_list = []
        dynamic_key_list = []
        for key, value in file_name_dict.items():
            #only_filename = re.split('/',i)[len(re.split('/',i)) - 1]
            only_filename = value
            path_without_filename = os.path.join(*re.split('/', i)[:-1])
            full_path = path_without_filename + "/" + only_filename
            filename_list = re.split('_',only_filename)
            num_ranks = filename_list[5]
            num_nodes = filename_list[3]
            files_per_rank = filename_list[7]

            #tmp_dict = {}
            with open (full_path, 'r') as file:
                for line in file:
                    tmp = line.strip().replace(':','')
                    line_list = re.split(r'[ \t]{2,}',tmp)
                    
                    if line_list[0] in key_list:
                        if line_list[0] == "Operation":
                            dynamic_key_list = line_list
                        else:
                            tmp_dict = {}
                            tmp_dict['operation'] = line_list[0]
                            tmp_dict['ranks_per_node'] = num_ranks
                            tmp_dict['node_count'] = num_nodes
                            tmp_dict['files_per_rank'] = files_per_rank
                            for el_index in range(len(line_list)): 
                                tmp_dict[dynamic_key_list[el_index]] = line_list[el_index]
                            if float(tmp_dict['Mean']) != 0:
                                tmp_list.append(tmp_dict)

        #print(tmp_list)
        df = pd.DataFrame(tmp_list)
        output_filename = file_name_dict["remove"].replace("Yur_","")
        json_data = df.to_json(f"{job_directory}/json_output/{output_filename}_dataframe.json", orient="records")

def convert_mdtest_data(job_directory):
    key_list = {"Directory creation",
            "Directory stat",
            "Directory removal",
            "File creation",
            "File stat",
            "File read",
            "File removal",
            "Tree creation",
            "Tree removal",
            "Operation"
            }
    values = ["Operation",
            "Max",
            "Min",
            "Mean",
            "Std Dev"
            ]
    
    if not os.path.exists(f"{job_directory}/json_output"):
        os.makedirs(f"{job_directory}/json_output")

    file_pattern = f"{job_directory}/mdtest*ranks*"
    files = glob.glob(file_pattern)

    for i in files:
        only_filename = re.split('/',i)[len(re.split('/',i)) - 1]
        filename_list = re.split('_',only_filename)
        num_ranks = filename_list[4]
        num_nodes = filename_list[2]
        files_per_rank = filename_list[6]

        #tmp_dict = {}
        tmp_list = []
        dynamic_key_list = []
        with open (i, 'r') as file:
            for line in file:
                tmp = line.strip().replace(':','')
                line_list = re.split(r'[ \t]{2,}',tmp)
                
                if line_list[0] in key_list:
                    if line_list[0] == "Operation":
                        dynamic_key_list = line_list
                    else:
                        tmp_dict = {}
                        tmp_dict['operation'] = line_list[0]
                        tmp_dict['ranks_per_node'] = num_ranks
                        tmp_dict['node_count'] = num_nodes
                        tmp_dict['files_per_rank'] = files_per_rank
                        for el_index in range(len(line_list)):
                            tmp_dict[dynamic_key_list[el_index]] = line_list[el_index]
                        tmp_list.append(tmp_dict)

            df = pd.DataFrame(tmp_list)
        json_data = df.to_json(f"{job_directory}/json_output/{only_filename}_dataframe.json", orient="records")

def read_mdtest_json_data(job_directory):
    json_dir = f"{job_directory}/json_output"

    #file_pattern = f"{json_dir}/mdtest*.json"
    file_pattern = f"{json_dir}/mdtest*dataframe.json"
    files = glob.glob(file_pattern)

    job_note_file = f"{job_directory}/job_note.txt"
    tmp_title = ''

    with open (job_note_file, 'r') as file:
        for line in file:
            if "PLOT TITLE" in line.upper() or "plot title" in line.lower():
                tmp_title = re.split(':', line)[1]
                plot_title = f"{tmp_title}"
            if tmp_title == '':
                print(f"Plot title not found for directory: {job_directory}")
                plot_title = "Title not found"

    one_job_result_list = []

    for i in files:
        #dict_list = []
        df = pd.DataFrame()
        #with open(i, 'r') as json_file:
        #    dict_list = json.load(json_file)     
        df = pd.read_json(i,orient="records")
        #print(df)
        #sys.exit()
        df['plot_title'] = plot_title            
        one_job_result_list.append(df)

    #print(all_result_list)
    return one_job_result_list 
