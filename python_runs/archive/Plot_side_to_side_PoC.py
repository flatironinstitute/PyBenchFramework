from parse_plot import load_json_files
from parse_plot import plot_data, parse_data
import re
import matplotlib.pyplot as plt

# Example usage


json_data = {}
directory_path = ['/mnt/home/skrit/Documents/PyBenchFramework/results/randwrite/storone/3520792/4_jobs_1M',
                  '/mnt/home/skrit/Documents/PyBenchFramework/results/randwrite/storone/3520792/8_jobs_1M',
                  '/mnt/home/skrit/Documents/PyBenchFramework/results/randwrite/storone/3520792/12_jobs_1M',
                  '/mnt/home/skrit/Documents/PyBenchFramework/results/randwrite/storone/3520792/16_jobs_1M',]

for item in directory_path:
    type_of_run = re.split(r'[/]\s*', item)
    type_of_run = type_of_run[len(type_of_run)-1]
    json_data[type_of_run] = load_json_files(item)

xmaster_list, ymaster_list, y2master_list, run_list = parse_data(json_data, "Random Writes (storone, 4K)", 'write')

json_data = {}
directory_path = ['/mnt/home/skrit/Documents/PyBenchFramework/results/randread/storone/3520792/4_jobs_1M',
                  '/mnt/home/skrit/Documents/PyBenchFramework/results/randread/storone/3520792/8_jobs_1M',
                  '/mnt/home/skrit/Documents/PyBenchFramework/results/randread/storone/3520792/12_jobs_1M',
                  '/mnt/home/skrit/Documents/PyBenchFramework/results/randread/storone/3520792/16_jobs_1M',]

for item in directory_path:
    type_of_run = re.split(r'[/]\s*', item)
    type_of_run = type_of_run[len(type_of_run)-1]
    json_data[type_of_run] = load_json_files(item)

x1master_list, y1master_list, y12master_list, run1_list = parse_data(json_data, "Random Reads (storone, 4K)", 'read')

# Show the plots when ready
#fig1.show()
#fig2.show()

#plt.ioff()

print(xmaster_list[0], ymaster_list[0], y2master_list[0], run_list)

#fig, (tmp_1, tmp_2) = plt.subplots(1, 2, figsize=(12, 6))
#fig2, ax = plt.subplots(1, 2, figsize=(12, 6))

#fig, ax = plt.subplots()

fig, (ax, ax3) = plt.subplots(1, 2, figsize=(12, 6))
ax2 = ax.twinx()

for i in range(len(xmaster_list)):
    ax.plot(xmaster_list[i], ymaster_list[i], 'o', label=run_list[i])
    ax2.plot(xmaster_list[i], y2master_list[i], 'o', label=run_list[i])
    
ax2.set_ylabel("IOPS")
ax.set_xlabel('Node count')
ax.set_ylabel('MB/s')
ax.set_title('read')
ax.legend(title='Type of run')
plt.xticks(rotation=45)
#plt.tight_layout()
#plt.show()


#fig2, ax3 = plt.subplots()
ax22 = ax3.twinx()

for i in range(len(x1master_list)):
    ax3.plot(x1master_list[i], y1master_list[i], 'o', label=run1_list[i])
    ax22.plot(x1master_list[i], y12master_list[i], 'o', label=run1_list[i])
    
ax22.set_ylabel("IOPS")
ax3.set_xlabel('Node count')
ax3.set_ylabel('MB/s')
ax3.set_title('read')
ax3.legend(title='Type of run')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
