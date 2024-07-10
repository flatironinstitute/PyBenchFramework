import glob
import json
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

#from collections import defaultdict, OrderedDict

# Directory containing the JSON files
#directory = "../results/write/EC63/3577299/"

def plot_serverless_FIO(directory):
    
    # Find all files matching the pattern "combined*.json"
    file_pattern = f"{directory}/combined*.json"
    files = glob.glob(file_pattern)

    # Dictionary to store parsed data
    data = {}

    # Parse each JSON file and store the data
    for file in files:
        tmplist = []
        with open(file, 'r') as f:
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
            bws.append(value[2]/1e6)
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
        ax1.plot(nodes_list[i], bw_list[i], 'o', label=f'{processor_counts[i]}_jobs')
        ax2.plot(nodes_list[i], iops_list[i], 'o', label=f'{processor_counts[i]}_jobs')

    ax2.set_ylabel("IOPS")
    ax1.set_xlabel('Node count')
    ax1.set_ylabel('GB/s')
    ax1.set_title('writes')
    ax1.legend(title='Type of run')
    plt.xticks(rotation=45)
    plt.tight_layout()
    # Set x-axis ticks to increment by 2
    plt.xticks(range(0, max(nodes_list[0])+1, 2))
    #plt.show()
    
    return fig, ax1, ax2