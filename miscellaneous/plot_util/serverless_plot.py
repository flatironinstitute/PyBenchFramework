import glob
import json
import matplotlib.pyplot as plt
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

#def plot_and_compare(first_result_list, second_result_list):
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
    
