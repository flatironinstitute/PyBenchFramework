import glob
import sys, os
import json
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MultipleLocator
import re

#from collections import defaultdict, OrderedDict

# Directory containing the JSON files
#directory = "../results/write/EC63/3577299/"

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

    #print(sorted_data)

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

    #print(sorted_data)

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
    return nodes_list, bw_list, iops_list, processor_counts

def mod_return_FIO_data(directory, title, block_size, benchmark, optional_plot_block_size=None):
    plot_title = []
    tmp_title = ''

    identifier = re.split('/', directory)[2]
    print(benchmark)
    if benchmark.upper() == "IOR" or benchmark.lower() == "ior":
        identifier = re.split('/', directory)[3]
        nodes_list, bw_list, iops_list, processor_counts = return_FIO_data(directory, title, block_size, "1M")
    else:
        nodes_list, bw_list, iops_list, processor_counts = return_FIO_data(directory, title, block_size)

    
    try:
        with open (f"{directory}/job_note.txt", 'r') as file:
            for line in file:
                if "PLOT TITLE" in line.upper() or "plot title" in line.lower():
                    tmp_title = re.split(':', line)[1]
                    plot_title.append(f"{identifier}-{tmp_title}")
            if tmp_title == '':
                print(f"Plot title not found for directory: {directory}")
                plot_title.append(f"{identifier}-Title not found")
    except FileNotFoundError:
        print(f"File {directory}/job_note.txt not found.")
        plot_title.append("Title not found")

    #print (nodes_list, bw_list, iops_list, processor_counts, plot_title)
    return nodes_list, bw_list, iops_list, processor_counts, plot_title

def plot_and_compare_mdtest(result_list, output_path):
    num_plots = len(result_list)
    print(num_plots)
    fig, axs = plt.subplots(1, num_plots, figsize=(7 * num_plots, 7), sharey=True)

    if num_plots ==1:
        axs = [axs]

    filename = []

    for idx,file_lists in enumerate(result_list):
        all_dict = {}
        ax = axs[idx]
        #for lists in file_lists:
        #print(file_lists)
        #print('')
        #print('')
        for dataframe in file_lists:
            tmp_list = []
            node_list = []
            ranks_per_node_list = []
            mean_performance_list = []
            #print(dataframe)
            #print(type(dataframe))
            #sys.exit()
            #print(dicts)
            #if dicts['operation'] == 'Directory creation':

            ranks_per_node = int(dataframe.loc[dataframe['operation'] == 'File creation', 'ranks_per_node'].values[0])
            node_count = int(dataframe.loc[dataframe['operation'] == 'File creation', 'node_count'].values[0])
            files_per_rank = float(dataframe.loc[dataframe['operation'] == 'File creation', 'files_per_rank'].values[0])
            mean_performance = float(dataframe.loc[dataframe['operation'] == 'File creation', 'Mean'].values[0])
            tmp_list.append(node_count)
            tmp_list.append(ranks_per_node)
            tmp_list.append(mean_performance)
            tmp_list.append(files_per_rank)

                #node_list.append(node_count)
                #mean_performance_list.append(mean_performance)
            if ranks_per_node not in all_dict:
                all_dict[ranks_per_node] = []
            #print(tmp_list)
            all_dict[ranks_per_node].append(tmp_list)
        #print(all_dict)
        sorted_data = {k: v for k, v in sorted(all_dict.items(), key=lambda item: item[0])}
        for key in sorted_data:
            sorted_data[key] = sorted(sorted_data[key], key=lambda x: x[0])
            #print(sorted_data[key])

        #print(sorted_data)
        #sys.exit()
    
        #from collections import OrderedDict
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
        
        #print(nodes_list, mean_perf_list, ranks_per_node_counts)
        for i in range(len(nodes_list)):
            ax.plot(nodes_list[i], mean_perf_list[i], '-o', label=f'{ranks_per_node_counts[i]}')

        ax.xaxis.set_major_locator(MultipleLocator(2))
        ax.set_xlabel('nodes')
        ax.set_ylabel('OPS/sec')
        ax.set_title('Directory Creation')
        ax.legend(title='Type of run')

    #filename.append()

    #filename = f"{filename1}_{filename2}"
    #final_filename = "_".join(filename)
    #print(final_filename)
    #final_filename = final_filename.replace(" ", "_")
    #final_filename = final_filename.replace("\n", "")
    #print(final_filename)
    final_filename = 'test_mdtest_dir_plotting'

    plt.savefig(f"{output_path}/{final_filename}.svg", format="svg")
    
def plot_and_compare(all_result_list, output_path):
    #Do I need lists or dicts of lists
    #How about two dicts that each have lists as values for each key?
    num_plots = len(all_result_list)  # Determine the number of plots needed
    print(num_plots)
    fig, axs = plt.subplots(1, num_plots, figsize=(7 * num_plots, 7), sharey=True)

    if num_plots == 1:
        axs = [axs]

    filename = []

    print(len(all_result_list))
    print(all_result_list)
    for idx, lists in enumerate(all_result_list):

        print(lists)
        print(len(lists))

        node_list, bw_list, iop_list, proc_list, plot_title = lists

        ax = axs[idx]

        for i in range(len(node_list)):
            ax.plot(node_list[i], bw_list[i], '-o', label=f'{proc_list[i]}_jobs')

        plot_title[0] = plot_title[0].replace("\n", "")
        ax.xaxis.set_major_locator(MultipleLocator(2))
        ax.set_xlabel('nodes')
        ax.set_ylabel('GB/s')
        ax.set_title(plot_title[0])
        ax.legend(title='Type of run')

        filename.append(re.split('-',plot_title[0].strip(" "))[0])
        #print(filename1)
        #print(filename2)

        #filename = f"{filename1}_{filename2}"
    final_filename = "_".join(filename)
    print(final_filename)
    final_filename = final_filename.replace(" ", "_")
    final_filename = final_filename.replace("\n", "")
    print(final_filename)

    plt.savefig(f"{output_path}/{final_filename}.svg", format="svg")
    
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

    one_job_result_list = []

    for i in files:
        #dict_list = []
        df = pd.DataFrame()
        #with open(i, 'r') as json_file:
        #    dict_list = json.load(json_file)     
        df = pd.read_json(i,orient="records")
        #print(df)
        #sys.exit()
        
        one_job_result_list.append(df)
    #print(all_result_list)
    return one_job_result_list 
