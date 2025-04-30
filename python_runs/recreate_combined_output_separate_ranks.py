import miscellaneous
import os
import datetime
import time
import json
import sys

block_sizes = ["4M"]
nodes = [24, 16, 8, 4, 2]
#proc = [16, 8, 4, 2]
proc = [16]
log_dir = sys.argv[1] 
#log_dir = "../results/read/Fi5-ec63-ssd-kernel/000000"
host_list = []
with open (f"{log_dir}/host_list", 'r') as f:
    for line in f:
        if line.strip() not in host_list:
            host_list.append(line.strip())

for node_iter in nodes:
    for block_size in block_sizes:
        for job_count in proc:
            
            for hostname in host_list:
                for local_rank in range(1,17):
                    json_log_file = f"{log_dir}/{hostname}_{local_rank}_{node_iter}_{job_count}p_{job_count}f_{block_size}.json"
                    print(json_log_file)
                    combined_json_log_file = f"{log_dir}/combined_{node_iter}_{job_count}p_{job_count}f_{block_size}.json"
                    uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"

                    if os.path.exists(json_log_file):
                        bw, iops = miscellaneous.load_json_results(json_log_file)

                        with open(uncombined_json_log_file, 'a') as file:
                            file.write(f"{hostname}, bw: {bw}, iops: {iops}, local rank: {local_rank}\n")
                    else:
                        print(f"[{hostname}] {local_rank} FIO JSON LOG FILE DOESN'T EXIST!!!")
                    #    sys.exit()
            
            file_count = job_count
            uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
            combined_json_log_file = f"{log_dir}/combined_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"

            bw_total = 0
            iops_total = 0

            with open (uncombined_json_log_file, 'r') as file:
                uncombined_dict = {}
                for line in file:
                    parts = line.split(',')
                    host = parts[0]
                    bw = float(parts[1].split(':')[1].strip())
                    iops = float(parts[2].split(':')[1].strip())

                    if host not in uncombined_dict:
                        uncombined_dict[host] = {'node_bw': 0, 'node_iops': 0}
                    uncombined_dict[host]['node_bw'] += bw
                    uncombined_dict[host]['node_iops'] += iops

                    bw_total += bw
                    iops_total += iops

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
                print(f"Data successfully written to {combined_json_log_file}")
