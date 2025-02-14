import os
import re
import socket
import handler_class
from datetime import datetime
import sys
import json
import benchmark_tools
import args_handler
import miscellaneous
#import network_counter_collection 
from network_collect import network_counter_collection
import threading
import time
import mmap
import count_lines_in_uncombined

block_sizes=["4M"]
log_dir = "../results/read/nvme_rep3_kernel/3706686"

for nodes in [20,16,8,4,2,1]:
    for block_size in block_sizes:
        for job_count in [48,16,8,4,2,1]:
            file_count = job_count
            json_log_file = f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
            combined_json_log_file = f"{log_dir}/combined_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
            uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
            if os.path.exists(json_log_file):
                bw, iops = miscellaneous.load_json_results(json_log_file)


            with open (uncombined_json_log_file, 'r') as file:
                for line in file:
                    parts = line.split(',')
                    bw = int(parts[1].split(':')[1].strip())
                    iops = float(parts[2].split(':')[1].strip())
                    bw_total += bw
                    iops_total += iops
            
            data = {
                    "nodes": node_iter,
                    "processors": job_count,
                    "bw": bw_total,
                    "iops": iops_total
            }

            with open(combined_json_log_file, 'w') as json_file:
                json.dump(data, json_file, indent=4)
                print(f"Data successfully written to {combined_json_log_file}")
