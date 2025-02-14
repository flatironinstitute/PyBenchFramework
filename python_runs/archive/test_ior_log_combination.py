import os
import socket
import handler_class
from datetime import datetime
import json
import sys
import yaml
import benchmark_tools
import args_handler
import miscellaneous
import network_collect
import threading
import time
import re
import shutil

block_size="4m"
log_dir = "../results/iortest/IOR_write/test-rep3-ssd/4037077/"

for nodes in [20,16,8,4,2,1]:
    for ranks in [48,16,8,4,2,1]:
        output_file=f"{log_dir}/ranks_per_node_{ranks}_node_count_{nodes}"
        #combined_json_log_file = f"{log_dir}/combined_{ranks}_{nodes}_{block_size}"
        json_log_file = output_file
        bw, iops = miscellaneous.load_ior_json_results(json_log_file, log_dir)
        #data = []
        for key, value in bw.items():
            combined_log_dir = f"../results/iortest/IOR_write/test-rep3-ssd/4037077/{key}"
            miscellaneous.ensure_log_directory_exists(combined_log_dir, 1)

            combined_json_log_file = f"{combined_log_dir}/combined_{ranks}_{nodes}_{block_size}"
            new_dict = {}
            new_dict = {"access": key, "nodes": nodes, "processors": ranks, "mbw": value, "iops": iops[key]}

            with open(combined_json_log_file, 'w') as json_file:
                json.dump(new_dict, json_file, indent=4)
                print(f"Data successfully written to {combined_json_log_file}")
