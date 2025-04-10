import miscellaneous
import os
from datetime import datetime
import time
import json

block_sizes = ["4M"]
nodes = [24, 16, 8, 4, 2]
proc = [16, 8, 4, 2]
log_dir = "../results/randwrite/Fi5-ec63-ssd-kernel/4159330/"
host_list = []
with open (f"{log_dir}/host_list", 'r') as f:
    for line in f:
        host_list.append(line.strip())

for node_iter in nodes:
    for block_size in block_sizes:
        for job_count in proc:
            for hostname in host_list:
                file_count = job_count
                json_log_file = f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                print(json_log_file)
                combined_json_log_file = f"{log_dir}/combined_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
                if os.path.exists(json_log_file):
                    bw, iops = miscellaneous.load_json_results(json_log_file)

                bw_total = 0
                iops_total = 0

                max_bw = 0
                min_bw = 0
                min_bw_counter = 0
                with open (uncombined_json_log_file, 'r') as file:
                    uncombined_dict = {}
                    for line in file:
                        parts = line.split(',')
                        bw = float(parts[1].split(':')[1].strip())
                        iops = float(parts[2].split(':')[1].strip())
                        bw_total += bw
                        iops_total += iops
                        uncombined_dict[parts[0]] = {
                                "node_bw": bw,
                                "node_iops": iops
                                }
                data = {
                        "nodes": node_iter,
                        "processors": job_count,
                        "bw": bw_total,
                        "iops": iops_total
                }
                data['node_list'] = {}
                for key, value in uncombined_dict.items():
                    data['node_list'][key] = value

                with open(combined_json_log_file, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                    print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Data successfully written to {combined_json_log_file}")
