import os
import json
import matplotlib.pyplot as plt
import pandas as pd

def load_json_files(directory):
    data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                try:
                    data[filename] = json.load(file)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {filename}")
    return data

import re

import matplotlib.pyplot as plt
import re

def plot_data(data, plot_title, job_type):
    # Turn off interactive mode
    plt.ioff()
    
    fig, ax = plt.subplots()
    ax2 = ax.twinx()
    i = 2
    x = []
    y = []
    y2 = []
    ndata = {}
    all_client_data = {}
    
    for type_of_run, run_dict in data.items():
        for key, json_dict in run_dict.items():
            result = re.split(r'[.]\s*', key)
            if len(json_dict['client_stats']) > 1:
                for j in range(len(json_dict['client_stats'])):
                    if json_dict['client_stats'][j]['jobname'] == 'All clients':
                        all_client_data[result[0]] = json_dict['client_stats'][j]
                node_count = len(json_dict['client_stats']) - 1
                IOPS = all_client_data[result[0]][job_type]['iops']
                ndata[result[0]] = [all_client_data[result[0]][job_type]['bw'] / 1024, node_count, IOPS]
            elif len(json_dict['client_stats']) == 1:
                all_client_data[result[0]] = json_dict['client_stats']
                node_count = len(json_dict['client_stats'])
                IOPS = all_client_data[result[0]][0][job_type]['iops']
                ndata[result[0]] = [all_client_data[result[0]][0][job_type]['bw'] / 1024, node_count, IOPS]

        sorted_data = sorted(ndata.items(), key=lambda item: item[1][0])
        sorted_dict = dict(sorted_data)

        for key, value in sorted_dict.items():
            x.append(value[1])
            y.append(value[0])
            y2.append(value[2])
            i += 2

        ax.plot(x, y, 'o', label=type_of_run)
        ax2.plot(x, y2, 'o', label='IOPS')

        ax2.set_ylabel("IOPS")

        ndata = {}
        x = []
        y = []
        y2 = []
        i = 2

    ax.set_xlabel('Node count')
    ax.set_ylabel('MB/s')
    ax.set_title(plot_title)
    ax.legend(title='Type of run')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Return the figure and axis objects
    return fig, ax, ax2

def parse_data(data, plot_title, job_type):
   
    i = 2
    xmaster_list = []
    ymaster_list = []
    y2master_list = []
    type_of_run_list = []
    
    x = []
    y = []
    y2 = []
    ndata = {}
    all_client_data = {}
    
    for type_of_run, run_dict in data.items():
        for key, json_dict in run_dict.items():
            result = re.split(r'[.]\s*', key)
            if len(json_dict['client_stats']) > 1:
                for j in range(len(json_dict['client_stats'])):
                    if json_dict['client_stats'][j]['jobname'] == 'All clients':
                        all_client_data[result[0]] = json_dict['client_stats'][j]
                node_count = len(json_dict['client_stats']) - 1
                IOPS = all_client_data[result[0]][job_type]['iops']
                ndata[result[0]] = [all_client_data[result[0]][job_type]['bw'] / 1024, node_count, IOPS]
            elif len(json_dict['client_stats']) == 1:
                all_client_data[result[0]] = json_dict['client_stats']
                node_count = len(json_dict['client_stats'])
                IOPS = all_client_data[result[0]][0][job_type]['iops']
                ndata[result[0]] = [all_client_data[result[0]][0][job_type]['bw'] / 1024, node_count, IOPS]

        sorted_data = sorted(ndata.items(), key=lambda item: item[1][0])
        sorted_dict = dict(sorted_data)

        for key, value in sorted_dict.items():
            x.append(value[1])
            y.append(value[0])
            y2.append(value[2])
            i += 2
        
        type_of_run_list.append(type_of_run)
        xmaster_list.append(x)
        ymaster_list.append(y)
        y2master_list.append(y2)
        
        ndata = {}
        x = []
        y = []
        y2 = []
        i = 2

    # Return the figure and axis objects
    return xmaster_list, ymaster_list, y2master_list, type_of_run_list, plot_title

# Load and parse data
def load_and_parse_data(directory_paths, plot_title, io_type):
    json_data = {}
    for item in directory_paths:
        type_of_run = re.split(r'[/]\s*', item)
        type_of_run = type_of_run[len(type_of_run)-1]
        json_data[type_of_run] = load_json_files(item)
    return parse_data(json_data, plot_title, io_type)

# Create a comparator engine
def compare_datasets(run_list1, x_list1, y_list1, y2_list1, run_list2, x_list2, y_list2, y2_list2):
    comparison_data = []
    for i in range(len(run_list1)):
        for j in range(len(x_list1[i])):
            run_type = run_list1[i]
            node_count = x_list1[i][j]
            y1 = y_list1[i][j]
            y2 = y2_list1[i][j]

            # Find the matching data point in the second dataset
            for k in range(len(run_list2)):
                if run_list2[k] == run_type:
                    for l in range(len(x_list2[k])):
                        if x_list2[k][l] == node_count:
                            y1_comp = y_list2[k][l]
                            y2_comp = y2_list2[k][l]
                            mb_speedup = (y1_comp - y1) / y1 * 100 if y1 != 0 else float('inf')
                            iops_speedup = (y2_comp - y2) / y2 * 100 if y2 != 0 else float('inf')
                            comparison_data.append({
                                'Run Type': run_type,
                                'Node Count': node_count,
                                'MB/s (5.15 kernel)': y1,
                                'MB/s (6.1 kernel)': y1_comp,
                                'MB/s Speedup (%)': mb_speedup,
                                'IOPS (5.15 kernel)': y2,
                                'IOPS (6.1 kernel)': y2_comp,
                                'IOPS Speedup (%)': iops_speedup
                            })
    return pd.DataFrame(comparison_data)

def comparison_plot(xmaster_list, ymaster_list, y2master_list, run_list, x1master_list, y1master_list, y12master_list, run1_list, plot_title, plot1_title):
    # Plotting the data
    fig, (ax, ax3) = plt.subplots(1, 2, figsize=(12, 6))
    ax2 = ax.twinx()

    for i in range(len(xmaster_list)):
        ax.plot(xmaster_list[i], ymaster_list[i], 'o', label=run_list[i])
        ax2.plot(xmaster_list[i], y2master_list[i], 'o', label=run_list[i])
    
    ax2.set_ylabel("IOPS")
    ax.set_xlabel('Node count')
    ax.set_ylabel('MB/s')
    ax.set_title(plot_title)
    ax.legend(title='Type of run')
    plt.xticks(rotation=45)

    ax22 = ax3.twinx()

    for i in range(len(x1master_list)):
        ax3.plot(x1master_list[i], y1master_list[i], 'o', label=run1_list[i])
        ax22.plot(x1master_list[i], y12master_list[i], 'o', label=run1_list[i])
    
    ax22.set_ylabel("IOPS")
    ax3.set_xlabel('Node count')
    ax3.set_ylabel('MB/s')
    ax3.set_title(plot1_title)
    ax3.legend(title='Type of run')
    plt.xticks(rotation=45)

    # Determine the maximum values for both sets of y-data
    max_y1 = max(max(y) for y in ymaster_list)
    max_y2 = max(max(y) for y in y2master_list)
    max_y3 = max(max(y) for y in y1master_list)
    max_y4 = max(max(y) for y in y12master_list)

    # Determine the 10% margin
    max_y = max(max_y1, max_y3) * 1.1
    max_y_secondary = max(max_y2, max_y4) * 1.1

    # Set the same y-limits for both plots
    ax.set_ylim(0, max_y)
    ax3.set_ylim(0, max_y)
    ax2.set_ylim(0, max_y_secondary)
    ax22.set_ylim(0, max_y_secondary)

    plt.tight_layout()
    plt.show()