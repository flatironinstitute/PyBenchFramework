import os
import json
import matplotlib.pyplot as plt

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