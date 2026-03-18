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
import threading
import time
import mmap
import count_lines_in_uncombined
import multi_level_barrier
from mpi4py import MPI
from analyze_and_rebalance_load import * 

def restart_ceph(args):
    if 'unit_restart' in args:
        if args['unit_restart'] == 1:
            split_dir = re.split('/', args['directory'])
            cephtest_root = '/'+split_dir[1]+'/'+split_dir[2]
            miscellaneous.restart_ceph_unit(cephtest_root)
            print(f"restarting the daemon on {hostname} from rank {rank}")

def test_wrap_tar(args, PyBench_root_dir):

    # Initialize MPI
    comm = MPI.COMM_WORLD    # Default communicator (all processes)
    rank = comm.Get_rank()   # Get the rank (ID) of this process
    size = comm.Get_size()   # Get the total number of processes

    job_number = args['slurm_job_number']
    log_dir = f"{PyBench_root_dir}/results/metadata/tar/{job_number}"
    
    if rank == 0:
        miscellaneous.ensure_log_directory_exists(log_dir,1)
    command_log_dir = f"{log_dir}/commands"

    today = datetime.date.today()
    hostname = socket.gethostname()
    
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

    # Set up the copy to /dev/shm
    initial_file_path = args['file_path']
    file_path_parts = re.split('/', initial_file_path) 

    filename = file_path_parts[len(file_path_parts) - 1]
    dev_shm_path = f"/dev/shm/{filename}"

    #create a map between hostnames and generic indexed hostnames
    if local_rank == 1:
        miscellaneous.create_hostname_mapping(log_dir,my_node_count)
        # Copy tar file to /dev/shm
        shutil.copy(initial_file_path, dev_shm_path)

    nodes = list(benchmark_tools.split_arg_sequence(str(args['node_count']), '--node-count'))
    proc = list(benchmark_tools.split_arg_sequence(args['job_number'], '--job-number'))
    tar_operations = list(benchmark_tools.split_block_size_sequence(args['tar_operations'], '--tar-operations'))

    tar_ob_dict = {}

    tar_directory = args['directory'] + f"/{hostname}_{local_rank}"
    compress_to = f"{hostname}_{local_rank}.tar"

    comm.Barrier()

    for node_iter in nodes:
            for job_count in proc:

                new_comm = {}
                print(f"{hostname}: My node count = {my_node_count} and my local rank = {local_rank}. iteration node count = {node_iter} and iteration job count = {job_count}")
                if my_node_count <= node_iter  and local_rank <= job_count:
                    iteration_comm = comm.Split(color=1,key=rank)
                else:
                    iteration_comm = comm.Split(color=MPI.UNDEFINED, key=rank)
                

                if iteration_comm != MPI.COMM_NULL:
                    
                    os.makedirs(tar_directory, exist_ok=False)
                    #just for organizational purposes, not related to actual mpi rank
                    global_rank = my_node_count * local_rank 

                    print(f"{hostname}: local rank: {local_rank}, my node count: {my_node_count}, global rank: {global_rank}, total node count: {node_iter}, ranks per node: {job_count}, io type: {args['io_type']}")
                    
                    file_count = job_count

                    tar_ob_name = f"{hostname}_{local_rank}_{node_iter}_{job_count}p_{file_count}f_{args['io_type']}"
                    tar_ob_dict[tar_ob_name] = handler_class.metadata_tar()
                    
                    tar_ob_dict[tar_ob_name].setup_command(output_file=f"{log_dir}/{hostname}_{local_rank}_{node_iter}_{job_count}p.json", tar_operation = 'extract', file_path = dev_shm_path, directory = tar_directory)

                    iteration_comm.Barrier()  # Wait for all processes to reach this point

                    extract_start_time = time.time()
                    tar_ob_dict[tar_ob_name].run()
                    extract_end_time = time.time()
                    extract_elapsed_time = extract_end_time - extract_start_time

                    time_dict = {
                            'hostname': hostname,
                            'node count': node_iter,
                            'job count': job_count,
                            'extract_start_time': extract_start_time,
                            'extract_end_time': extract_end_time,
                            'extract_elapsed_time': extract_elapsed_time}

                    if local_rank == 1:
                        restart_ceph(args)

                    iteration_comm.Barrier()  # Wait for all processes to reach this point

                    if 'compress' in tar_operations:
                        tar_ob_dict[tar_ob_name].setup_command(output_file=f"{log_dir}/{hostname}_{local_rank}_{node_iter}_{job_count}p.json", tar_operation = 'compress', file_path = f"/dev/null", directory = tar_directory)

                        iteration_comm.Barrier()  # Wait for all processes to reach this point
                        compress_start_time = time.time()
                        tar_ob_dict[tar_ob_name].run()
                        compress_end_time = time.time()
                        compress_elapsed_time = compress_end_time - compress_start_time
                        time_dict['compress_start_time'] = compress_start_time
                        time_dict['compress_end_time'] = compress_end_time
                        time_dict['compress_elapsed_time'] = compress_elapsed_time

                    if local_rank == 1:
                        restart_ceph(args)

                    iteration_comm.Barrier()  # Wait for all processes to reach this point

                    delete_start_time = time.time()
                    shutil.rmtree(tar_directory)
                    delete_end_time = time.time()
                    delete_elapsed_time = delete_end_time - delete_start_time

                    time_dict['delete_start_time'] = delete_start_time
                    time_dict['delete_end_time'] = delete_end_time
                    time_dict['delete_elapsed_time'] = delete_elapsed_time

                    with open (f"{log_dir}/{hostname}_{local_rank}_{node_iter}_{job_count}p.json", 'w') as f:
                        json.dump(time_dict, f, indent=4)

                    if local_rank == 1:
                        restart_ceph(args)

                    iteration_comm.Barrier()  # Wait for all processes to reach this point
                    time.sleep(5)
