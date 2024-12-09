import os
import fcntl
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

def count_lines_in_file(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return len(lines)
    except FileNotFoundError:
        return 0

def wait_until_line_count_is_node_count(file_path, hostname, node_count, check_interval=1):
    line_count = count_lines_in_file(file_path)
    
    wait_time = 0
    while line_count != node_count:
        print(f"Current line count is {line_count}. Waiting...")
        time.sleep(check_interval)
        line_count = count_lines_in_file(file_path)
        wait_time += 1
        if wait_time >= 600:
            print ("Waited too long for uncombined to have the correct number of lines. Jobs and nodes are out of sync by over 10 minutes")
            sys.exit(1)
    
    print(f"{hostname} uncombined file has reached {node_count} lines. Moving onto next job...")

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
    
    #create a map between hostnames and generic indexed hostnames
    miscellaneous.create_hostname_mapping(log_dir)

    if 'job_note' in args.keys():
        job_note = f"{args['job_note']} {args['io_type']}"
        with open(f"{log_dir}/job_note.txt", 'w') as file:
            file.write(job_note)

    if args['file_size']:
        pass
    else:
        print( "Must specify a file size for FIO to write out..." )
        sys.exit()

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
                    file_contents = miscellaneous.reset_file_contents(original_file_contents, args, job_count, block_size,log_dir)

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
                    
                    json_log_file = f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                    uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
                    
                    wait_res = 0
                    while wait_res == 0:
                        if os.path.exists(json_log_file):
                            bw, iops = miscellaneous.load_json_results(json_log_file)

                            with open(uncombined_json_log_file, 'a') as file:
                                fcntl.flock(file, fcntl.LOCK_EX)  # Lock the file for exclusive access
                                file.write(f"{hostname}, bw: {bw}, iops: {iops} \n")
                                fcntl.flock(file, fcntl.LOCK_UN)  # Unlock the file after writing

                        if 'wait_for_others' in args.keys():
                            if args['wait_for_others']:
                                wait_res = count_lines_in_uncombined.wait_until_line_count_is_node_count(uncombined_json_log_file, hostname, node_iter, 1000)
                            else:
                                wait_res = count_lines_in_uncombined.wait_until_line_count_is_node_count(uncombined_json_log_file, hostname, node_iter, 100)

                    if 'unit_restart' in args:
                        if args['unit_restart'] == 1:
                            pattern = '/'
                            split_dir = re.split(pattern, args['directory'])
                            cephtest_root = '/'+split_dir[1]+'/'+split_dir[2]
                            miscellaneous.restart_ceph_unit(cephtest_root)
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

                    #with open(uncombined_json_log_file, 'a') as file:
                    #    file.write(f"{hostname}, bw: {bw}, iops: {iops} \n")

                    #time.sleep(5)

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
                

