import matplotlib.pyplot as plt
import re
import pandas as pd
import glob

def read_between_markers(filename, start_marker, end_marker):
    with open(filename, 'r') as file:
        lines = file.readlines()
    
    start_index = None
    end_index = None
    
    for i, line in enumerate(lines):
        if start_marker in line and start_index is None:
            start_index = i
        if end_marker in line and start_index is not None:
            end_index = i - 1
            break
    
    if start_index is not None and end_index is not None:
        return lines[start_index:end_index + 1]
    else:
        return []

# Find all files matching the pattern "combined*.json"
directory = "../results/metadata/kernel_EC63/3635332"
file_pattern = f"{directory}/mdtest_output_*"
files = glob.glob(file_pattern)

# Dictionary to store parsed data
data = {}
start_marker = 'Operation'
end_marker = '-- finished at'
split_lines = []

# Parse each JSON file and store the data
for file in files:
    lines_between = read_between_markers(file, start_marker, end_marker)
    for line in lines_between:
        split_lines.append(line.split())
    dict_key_list = re.split('_', file)
    #dict_key = dict_key_list[3]+"r_"+dict_key_list[5]+"f"    
    dict_key = int(dict_key_list[3]),int(dict_key_list[5])
    data[dict_key] = pd.DataFrame(split_lines)
    split_lines = []

dict_of_file_creation = {}

for key, value in data.items():
    dict_of_file_creation[key] = value[3][6]

# Sort the dictionary items first by the second element, then by the first element of the tuple key
sorted_items = sorted(dict_of_file_creation.items(), key=lambda item: (item[0][1], item[0][0]))

# Convert the sorted items into a list of lists
sorted_list_of_lists = [[k[0], k[1], v] for k, v in sorted_items]

fig, ax = plt.subplots()
second_values = sorted(set([d[1] for d in sorted_list_of_lists]))
#print(second_values)
# Plot each group of data with the same second value in the tuple

for second_value in second_values:
    subset = [d for d in sorted_list_of_lists if d[1] == second_value]
    x = [d[0] for d in subset]
    y = [float(d[2]) for d in subset]
    ax.plot(x, y, marker='o', linestyle='-', label=f'{second_value}')

# Customizing the plot
ax.set_xlabel('Ranks')
ax.set_ylabel('ops/sec')
ax.set_title('File creation')
ax.legend(title='Files per rank')
plt.show()
