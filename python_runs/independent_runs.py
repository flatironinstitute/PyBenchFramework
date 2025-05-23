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
import multi_level_barrier
from mpi4py import MPI

def serverless_fio(args, PyBench_root_dir):
    #testing mpi
    # Initialize MPI
    comm = MPI.COMM_WORLD    # Default communicator (all processes)
    rank = comm.Get_rank()   # Get the rank (ID) of this process
    size = comm.Get_size()   # Get the total number of processes
    #finished mpi section

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
    miscellaneous.create_hostname_mapping(log_dir,rank)

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

    #Is this still needed (probably not)?
    my_line_num = miscellaneous.grep_string(node_split_file, hostname)

    #as job progesses iteration count increases
    iteration_count = 0

    for node_iter in nodes:
        #TESTING MPI BARRIER
        #replace this with if my rank + 1 <= node_iter
        #if my_line_num <= node_iter:
        #if rank <= node_iter - 1:
        # Create a new communicator for the selected ranks
        if rank <= node_iter - 1:
            new_comm = comm.Split(color=1, key=rank)  # Grouping ranks > some_count
        else:
            new_comm = comm.Split(color=MPI.UNDEFINED, key=rank)  # Exclude ranks <= some_count

        if new_comm != MPI.COMM_NULL:
            for block_size in block_sizes:
                #print(f"This iteration's block size is: {block_size}")
                for job_count in proc:
                    
                    file_count = job_count

                    #Reset file contents for FIO config file
                    file_contents = miscellaneous.reset_file_contents(original_file_contents, args, job_count, block_size,log_dir)
                    fio_job_config = f"{PyBench_root_dir}/examples/test_files/{job_number}_{hostname}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}.fio"
                    with open(fio_job_config, 'w') as file:
                        file.write(file_contents)

                    fio_ob_name = f"{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}"
                    fio_ob_dict[fio_ob_name] = handler_class.FIOTool()
                    
                    fio_ob_dict[fio_ob_name].setup_command(config_file=fio_job_config, output_format="json", output_file=f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json")

                    with open(f"{command_log_dir}/{job_number}_{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['platform_type']}_command", 'a') as file:
                        file.write(f"num nodes is 1, job number is {job_count}")
                        tmp_cmd_string = ""
                        for cmd_el in fio_ob_dict[fio_ob_name].command:
                            tmp_cmd_string += f" {cmd_el}"
                        file.write(tmp_cmd_string)

                    network_counter_collection.stop_thread = False
                    background_thread = threading.Thread(target=background_network_monitor, args=(args, job_count, node_iter, block_size, PyBench_root_dir))
                    background_thread.start()
                    start_time = time.time()
                    #TESTING MPI BARRIER
                    # Synchronize all processes at the barrier
                    print(f"Process {rank} is reaching the barrier.")
                    new_comm.Barrier()  # Wait for all processes to reach this point

                    # Once the barrier is passed, all processes continue
                    #current_time = time.time()
                    print(f"Process {rank} has passed the barrier. {time.time()}")

                    # Continue with the rest of the code after the barrier

                    print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] starting fio Job num: {job_count}, node count: {node_iter}, IO type {args['io_type']} {time.time()}")
                    fio_ob_dict[fio_ob_name].run()
                    print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] stopping fio Job num: {job_count}, node count: {node_iter}, IO type {args['io_type']} {time.time()}")
                    network_counter_collection.stop_thread = True
                    background_thread.join()
                    end_time = time.time()

                    elapsed_time = end_time - start_time
                    print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Job num: {job_count}, node count: {node_iter}. Iteration is finished. {hostname} [s-{start_time}], [e-{end_time}, el-{elapsed_time}]")
                    
                    json_log_file = f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                    uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
                    first_barrier_file = f"{log_dir}/barrier_file_1_{iteration_count}.txt"
                    second_barrier_file = f"{log_dir}/barrier_file_2_{iteration_count}.txt"
                    
                    if 'unit_restart' in args:
                        if args['unit_restart'] == 1:
                            pattern = '/'
                            split_dir = re.split(pattern, args['directory'])
                            cephtest_root = '/'+split_dir[1]+'/'+split_dir[2]
                            miscellaneous.restart_ceph_unit(cephtest_root)

                    #wait_res = 0
                    #while wait_res == 0:
                    if os.path.exists(json_log_file):
                        bw, iops = miscellaneous.load_json_results(json_log_file)

                        with open(uncombined_json_log_file, 'a') as file:
                            fcntl.flock(file, fcntl.LOCK_EX)  # Lock the file for exclusive access
                            file.write(f"{hostname}, bw: {bw}, iops: {iops} \n")
                            fcntl.flock(file, fcntl.LOCK_UN)  # Unlock the file after writing
                    else:
                        print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] FIO JSON LOG FILE DOESN'T EXIST!!! - iteration {iteration_count}")
                        sys.exit()

                    #This is wrong I think. Needs to change to a barrier outside of any iteration and before any log combination/modification. It still works because rank 0 is the only rank taking action after the iterations but... Either way it works... Just think about whether this is the spot to put it and about whether it's this communicator or the default communicator that should be used. 
                    new_comm.Barrier()  # Wait for all processes to reach this point

                    #Probably remove this
                    '''
                    if 'wait_for_others' in args.keys():
                        # B) Barrier Phase=1: "Done with iteration i"
                        multi_level_barrier.barrier_phase(first_barrier_file, iteration_count, hostname, phase=1, node_count=node_iter)

                        # C) Barrier Phase=2: "Ready for iteration i+1"
                        #    This ensures that *every node* knows that every other node has finished iteration i.
                        multi_level_barrier.barrier_phase(second_barrier_file, iteration_count, hostname, phase=2, node_count=node_iter)
                    iteration_count += 1
                    #BETWEEN BARRIER AND ORIGINAL FILE_BASED WAITING
                    if args['wait_for_others']:
                        wait_res = count_lines_in_uncombined.wait_until_line_count_is_node_count(uncombined_json_log_file, hostname, node_iter, 1000)
                    else:
                        wait_res = count_lines_in_uncombined.wait_until_line_count_is_node_count(uncombined_json_log_file, hostname, node_iter, 100)
                    '''
                    #sys.stdout.flush()
                    print("Sleeping for 15 seconds...")
                    time.sleep(15)
                    

    #probably change this so that only rank 0 executes anything
    for node_iter in nodes:
        for block_size in block_sizes:
            for job_count in proc:
                file_count = job_count
                json_log_file = f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                combined_json_log_file = f"{log_dir}/combined_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
                if os.path.exists(json_log_file):
                    bw, iops = miscellaneous.load_json_results(json_log_file)

                if rank == 0:
                    bw_total = 0
                    iops_total = 0

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
                

