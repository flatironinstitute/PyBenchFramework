import os
import fcntl
import re
import socket
import shutil
import handler_class
#from datetime import datetime
import datetime
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
from analyze_and_rebalance_load import * 

def independent_ranks(args, PyBench_root_dir):
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

    today = datetime.date.today()
    formatted = today.strftime("%m/%d/%Y")  # e.g. "03/19/2025"
    
    if 'job_note' in args.keys():
        job_note = f"{args['job_note']} {args['io_type']} {formatted}"
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
    
    # 1) Get this rank’s hostname
    hostname = socket.gethostname()

    # 2) Gather all hostnames
    all_hostnames = comm.allgather(hostname)

    # 3) Build a sorted list of unique hostnames
    unique_hosts = sorted(set(all_hostnames))

    # 4) Create a dict mapping each hostname to a 0-based index
    host_to_index = {host: i for i, host in enumerate(unique_hosts)}

    # Assign our node index to my_node_count
    my_node_count = host_to_index[hostname] + 1
    #my_node_count = int(os.environ["OMPI_COMM_WORLD_NODE_RANK"]) + 1
    local_rank = int(os.environ["OMPI_COMM_WORLD_LOCAL_RANK"]) + 1

    #create a map between hostnames and generic indexed hostnames
    if local_rank == 1:
        miscellaneous.create_hostname_mapping(log_dir,my_node_count)

    # copy YAML config file to output directory for extra logging
    if local_rank == 1 and my_node_count == 1:
        if os.path.isfile(args['config']):
            shutil.copy(args['config'],log_dir) 

    start_and_end_path = f"{log_dir}/start_and_end_times"
    if local_rank == 1 and my_node_count == 1:
        #start_and_end_path = f"{log_dir}/start_and_end_times"
        if not os.path.exists(start_and_end_path):
            os.mkdir(start_and_end_path)


    for node_iter in nodes:
        #TESTING MPI BARRIER
        #replace this with if my rank + 1 <= node_iter
        #if my_line_num <= node_iter:
        #if rank <= node_iter - 1:
        # Create a new communicator for the selected ranks

        for block_size in block_sizes:
            for job_count in proc:
                #print(f"This iteration's block size is: {block_size}")
                new_comm = {}
                #print(f"{hostname}: My node count = {my_node_count} and my local rank = {local_rank}. iteration node count = {node_iter} and iteration job count = {job_count}")
                if my_node_count <= node_iter  and local_rank <= job_count:
                    #new_comm[my_node_count] = comm.Split(color=my_node_count+1, key=rank)  # Grouping ranks > some_count
                    iteration_comm = comm.Split(color=1,key=rank)
                else:
                    #new_comm[my_node_count] = comm.Split(color=MPI.UNDEFINED, key=rank)  # Exclude ranks <= some_count
                    iteration_comm = comm.Split(color=MPI.UNDEFINED, key=rank)
                

                if iteration_comm != MPI.COMM_NULL:
                    
                    #just for organizational purposes, not related to actual mpi rank
                    global_rank = my_node_count * local_rank 

                    #print(f"{hostname}: local rank: {local_rank}, my node count: {my_node_count}, global rank: {global_rank}, total node count: {node_iter}, ranks per node: {job_count}, io type: {args['io_type']}")
                    
                    file_count = job_count

                    #Reset file contents for FIO config file
                    file_contents = miscellaneous.reset_file_contents(original_file_contents, args, 1, block_size,log_dir,local_rank)
                    fio_job_config = f"{PyBench_root_dir}/examples/test_files/{job_number}_{hostname}_{local_rank}_{node_iter}n_{job_count}p_{file_count}f_{block_size}_{args['io_type']}.fio"
                    with open(fio_job_config, 'w') as file:
                        file.write(file_contents)

                    fio_ob_name = f"{hostname}_{local_rank}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['io_type']}"
                    fio_ob_dict[fio_ob_name] = handler_class.FIOTool()
                    
                    fio_ob_dict[fio_ob_name].setup_command(config_file=fio_job_config, output_format="json", output_file=f"{log_dir}/{hostname}_{local_rank}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json")

                    with open(f"{command_log_dir}/{job_number}_{hostname}_{local_rank}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['platform_type']}_command", 'a') as file:
                        file.write(f"num nodes is {node_iter}, job number is {job_count}")
                        tmp_cmd_string = ""
                        for cmd_el in fio_ob_dict[fio_ob_name].command:
                            tmp_cmd_string += f" {cmd_el}"
                        file.write(tmp_cmd_string)

    
                    #network_counter_collection.stop_thread = False
                    #background_thread = threading.Thread(target=background_network_monitor, args=(args, job_count, node_iter, block_size, PyBench_root_dir))
                    #background_thread.start()
                    start_time = time.time()
                    #TESTING MPI BARRIER
                    # Synchronize all processes at the barrier
                    #print(f"rank {local_rank} on node {my_node_count} is reaching the barrier.")

                    # Once the barrier is passed, all processes continue
                    #current_time = time.time()
                    #print(f"rank {local_rank} on node {my_node_count} has passed the barrier. {time.time()}")

                    # Continue with the rest of the code after the barrier

                    iteration_comm.Barrier()  # Wait for all processes to reach this point
                    start_time = time.time()
                    starting_statement = f"{datetime.datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] starting fio Job num: {job_count}, node count: {node_iter}, local rank {local_rank}, node count {my_node_count}, IO type {args['io_type']} {time.time()} \n"
                    fio_ob_dict[fio_ob_name].run()
                    end_time = time.time()
                    ending_statement = f"{datetime.datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] stopping fio Job num: {job_count}, node count: {node_iter}, local rank {local_rank}, node count {my_node_count}, IO type {args['io_type']} {time.time()} \n"

                    '''
                    if rank == my_node_count*1 - 1:
                        #print(f"rank {rank} from node count: {my_node_count} wants to receive.")
                        #combined_start_times = []
                        combined_times = []
                        combined_times.append((hostname, rank, start_time, end_time))
                        receive_list = []
                        previous_rank = 0

                        for i in range(job_count - 1):
                            if i == 0:
                                receive_list.append(rank + node_iter)
                            else:
                                receive_list.append(receive_list[i-1] + node_iter)

                        #print(f"rank: {rank}, receive_list = {receive_list}")
                        for source_rank in receive_list:
                            rank_start_and_end = iteration_comm.recv(source=(source_rank), tag=0)
                            combined_times.append(rank_start_and_end)
                            #print(f"{rank} received {rank_start_and_end} from source rank {source_rank}")
                            #print(f"Rank:  wants to receive data from source rank: {source_rank - 1}")
                            #combined_end_times.append([f"{local_rank}_end": end_time])

                        
                        with open(f"{start_and_end_path}/{job_number}_{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}_{args['platform_type']}_times", 'a') as file:
                            json.dump(combined_times, file, indent=4)
                    ''' 
                    if rank != 0:
                        combined_times = (hostname, rank, start_time, end_time)
                        iteration_comm.send(combined_times, dest=0, tag=0)
                        #iteration_comm.send((hostname, rank, start_time, end_time), dest=(my_node_count*1 - 1), tag=0)
                        #print(f"Rank: {rank} wants to send data to rank:{my_node_count*1 - 1}")
                    else:
                        start_end_times_list = []

                        for i in range(iteration_comm.Get_size()):
                            #print(i)
                            if i != 0:
                                start_end_times_list.append(iteration_comm.recv(source=i, tag=0))
                    
                    iteration_comm.Barrier()

                    #print(starting_statement)
                    #print(ending_statement)
                    
                    if rank == 0:
                        #log_and_analyze_data_points(log_dir, fio_ob_dict[fio_ob_name],start_end_times_list)
                        log_and_analyze_data_points(log_dir, fio_ob_dict[fio_ob_name])
                    #network_counter_collection.stop_thread = True
                    #background_thread.join()
                    #end_time = time.time()

                    #elapsed_time = end_time - start_time
                    #print(f"{datetime.datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Job num: {job_count}, node count: {node_iter}. Iteration is finished. {hostname} [s-{start_time}], [e-{end_time}, el-{elapsed_time}]")
                    
                    json_log_file = f"{log_dir}/{hostname}_{local_rank}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                    uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"
                    #first_barrier_file = f"{log_dir}/barrier_file_1_{iteration_count}.txt"
                    #second_barrier_file = f"{log_dir}/barrier_file_2_{iteration_count}.txt"
                    
                    if local_rank == 1:
                        if 'unit_restart' in args:
                            if args['unit_restart'] == 1:
                                pattern = '/'
                                split_dir = re.split(pattern, args['directory'])
                                cephtest_root = '/'+split_dir[1]+'/'+split_dir[2]
                                miscellaneous.restart_ceph_unit(cephtest_root)
                                print(f"restarting the daemon on {hostname} from rank {rank}")

                    #wait_res = 0
                    #while wait_res == 0:
                    if os.path.exists(json_log_file):
                        bw, iops = miscellaneous.load_json_results(json_log_file)

                        with open(uncombined_json_log_file, 'a') as file:
                            fcntl.flock(file, fcntl.LOCK_EX)  # Lock the file for exclusive access
                            file.write(f"{hostname}, bw: {bw}, iops: {iops}, local rank: {local_rank}\n")
                            fcntl.flock(file, fcntl.LOCK_UN)  # Unlock the file after writing
                    else:
                        print(f"{datetime.datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] {local_rank} FIO JSON LOG FILE DOESN'T EXIST!!! - iteration {iteration_count}")
                        sys.exit()

                    #This is wrong I think. Needs to change to a barrier outside of any iteration and before any log combination/modification. It still works because rank 0 is the only rank taking action after the iterations but... Either way it works... Just think about whether this is the spot to put it and about whether it's this communicator or the default communicator that should be used. 
                    iteration_comm.Barrier()  # Wait for all processes to reach this point

                    #Probably remove this
                    #sys.stdout.flush()
                    #print("Sleeping for 15 seconds...")
                    time.sleep(5)
                    
     
    #probably change this so that only rank 0 executes anything
    for node_iter in nodes:
        for block_size in block_sizes:
            for job_count in proc:
                if local_rank == 1 and my_node_count == 1:
                    file_count = job_count
                    json_log_file = f"{log_dir}/{hostname}_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                    combined_json_log_file = f"{log_dir}/combined_{node_iter}_{job_count}p_{file_count}f_{block_size}.json"
                    uncombined_json_log_file = f"{log_dir}/uncombined_{node_iter}_{job_count}p_{block_size}.tmp"

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
                        print(f"{datetime.datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Data successfully written to {combined_json_log_file}")
                    
