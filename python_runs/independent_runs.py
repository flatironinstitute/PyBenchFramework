import os
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

def serverless_fio(args, PyBench_root_dir):
    def background_network_monitor(args, job_count, node_count, block_size, PyBench_root_dir):
            print("network_monitoring")
            network_counter_collection.monitor_traffic(args, job_count, node_count, block_size, PyBench_root_dir)

    job_number = args['slurm_job_number']
    total_node_count = int(args['total_node_count'])
    
    fio_ob_dict = {}
    fio_out_dict = {}

    proc = list(benchmark_tools.split_arg_sequence(args['job_number'], '--job-number')) 
    nodes = list(benchmark_tools.split_arg_sequence(str(args['node_count']), '--node-count'))
    block_sizes = benchmark_tools.split_block_size_sequence(args['block_size'], '--block-size')
    #print(f"{block_sizes} type is {type(block_sizes)}")

    config_template_path = args['template_path']

    with open(config_template_path, 'r') as file:
        original_file_contents = file.read()

    log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    
    hostname = socket.gethostname()
    
    #put this code into miscellaneous
    node_split_file = f"{log_dir}/host_list"
    miscellaneous.insert_entry_and_check_completion(node_split_file, hostname, total_node_count)

    my_line_num = miscellaneous.grep_string(node_split_file, hostname)

    for node_iter in nodes:
        if my_line_num <= node_iter:
            for block_size in block_sizes:
                #print(f"This iteration's block size is: {block_size}")
                for job_count in proc:
                    
                    file_count = job_count

                    #Reset file contents for FIO config file
                    file_contents = miscellaneous.reset_file_contents(original_file_contents, args, job_count, block_size)

                    with open(f"examples/test_files/{job_number}_{hostname}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}.fio", 'w') as file:
                        file.write(file_contents)

                    fio_ob_dict[f"{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}"] = handler_class.FIOTool()
                    
                    fio_ob_dict[f"{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}"].setup_command(config_file=f"{PyBench_root_dir}/examples/test_files/{job_number}_{hostname}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}.fio", output_format="json", output_file=f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json")

                    with open(f"{command_log_dir}/{job_number}_{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['platform_type']}_command", 'a') as file:
                        file.write(f"num nodes is 1, job number is {job_count}")
                        tmp_cmd_string = ""
                        for cmd_el in fio_ob_dict[f"{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}"].command:
                            tmp_cmd_string += f" {cmd_el}"
                        file.write(tmp_cmd_string)

                    network_counter_collection.stop_thread = False
                    background_thread = threading.Thread(target=background_network_monitor, args=(args, job_count, node_iter, block_size, PyBench_root_dir))
                    background_thread.start()
                    start_time = time.time()
                    print("starting fio?")
                    fio_ob_dict[f"{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}"].run()
                    print("stopping fio?")
                    network_counter_collection.stop_thread = True
                    background_thread.join()
                    end_time = time.time()

                    elapsed_time = end_time - start_time
                    print(f"Job num: {job_count}, node count: {node_iter}. Iteration is finished. {hostname} [s-{start_time}], [e-{end_time}, el-{elapsed_time}]")
                    
                    sys.stdout.flush()
            
    for node_iter in nodes:
        for block_size in block_sizes:
            for job_count in proc:
                file_count = job_count
                json_log_file = f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                combined_json_log_file = f"{log_dir}/combined_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
                if os.path.exists(json_log_file):
                    bw, iops = miscellaneous.load_json_results(json_log_file)

                    with open(uncombined_json_log_file, 'a') as file:
                        file.write(f"{hostname}, bw: {bw}, iops: {iops} \n")

                    time.sleep(5)

                if my_line_num == 1:
                    bw_total = 0
                    iops_total = 0

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
