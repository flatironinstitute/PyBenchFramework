import os
import socket
import handler_class
from datetime import datetime
import sys
import benchmark_tools
import args_handler
import miscellaneous
import network_collect 
import threading
import time
import re
import shutil

def wrap_mdtest(args, PyBench_root_dir):

    job_number = args['slurm_job_number']

    current_dir = os.getcwd()

    mdtest_obj_dict = {}
    #handler_class.mdtestTool()

    log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    tmp_log_dir = f"{log_dir}/tmp_files"
    
    hostname = socket.gethostname()

    mpi_ranks = sorted(benchmark_tools.split_arg_sequence(args['mpi_ranks'], "--mpi-ranks"))
    files_per_rank_list = sorted(benchmark_tools.split_arg_sequence(args['files_per_rank'], "--files-per-rank"))
    test_repetition = args['test_repetition']
    directory = args['directory']
    offset = args['offset']
    write_data = args['write_data']
    read_data = args['read_data']
    node_count = sorted(benchmark_tools.split_arg_sequence(args['node_count'], "--node-count"))

    total_files_optimized = 0
    
    if args['timed']:
        times = sorted(benchmark_tools.split_arg_sequence(args['timed'], "--timed"))
        if len(times) != 2:
            print ( f"When using the 'timed' option, please ensure to specify two comma-delimited integer values indicating a lower threshold and upper threshold of time in seconds that the test should run for. Values as interpreted are: {times}" )
            sys.exit()
        lower_time_threshold = times[0]
        upper_time_threshold = times[1]

    for node in node_count:
        for rank in mpi_ranks:
            tmp_rank = int(rank)
            node_type = int(node)
            tmp_rank = node_type * tmp_rank
            ranks_per_node = int(tmp_rank / node_type)
            for files_per_rank in files_per_rank_list:
                if total_files_optimized != 0:
                    files_per_rank = total_files_optimized / tmp_rank

                out_file = f"{log_dir}/mdtest_output_{node_type}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"

                print (f"ranks per node are {ranks_per_node} and type is {type(ranks_per_node)}, nodes are {node_type} and type is {type(node_type)}")
                mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"] = handler_class.mdtestTool()

                mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].setup_command(config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{files_per_rank}", test_repetition=f"{test_repetition}", directory=f"{directory}", offset=f"{offset}", output_file=out_file, write_data=f"{write_data}", read_data=f"{read_data}", ranks_per_node=f"{ranks_per_node}", write_output=1)
            
                with open(f"{command_log_dir}/mdtest_command_{node_type}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank", 'a') as file:
                    file.write(f"The following is the mdtest command")
                    tmp_cmd_string = ""
                    for cmd_el in mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].command:
                        tmp_cmd_string += f" {cmd_el}"
                    file.write(tmp_cmd_string)
                
                mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].run()
                
                start_time, end_time, elapsed_time = benchmark_tools.mdtest_start_end_elapsed_time(out_file)
                
                if args['timed']:
                    #elapsed_time, out_file, tmp_log_dir, tmp_log_filename, lower_threshold, higher_threshold, log_dir, args, among others
                    if elapsed_time <= lower_time_threshold or elapsed_time >= upper_time_threshold:
                        while elapsed_time <= lower_time_threshold or elapsed_time >= upper_time_threshold:
                            source = out_file
                            tmp_log_filename = re.split('/', out_file)[len(re.split('/', out_file)) - 1]
                            destination = f"{tmp_log_dir}/{tmp_log_filename}"
                            shutil.move(source, destination)
                            
                            if elapsed_time <= lower_time_threshold:
                                multiple = lower_time_threshold / elapsed_time
                                new_files_per_rank = int(files_per_rank * multiple) + int(0.05 * files_per_rank)
                            if elapsed_time >= upper_time_threshold:
                                multiple = upper_time_threshold / elapsed_time
                                new_files_per_rank = int(files_per_rank * multiple) - int(0.05 * files_per_rank)

                            out_file = f"{log_dir}/mdtest_output_{node_type}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank_timed"
                            
                            mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"] = handler_class.mdtestTool()
                            mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"].setup_command(config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{new_files_per_rank}", test_repetition=f"{test_repetition}", directory=f"{directory}", offset=f"{offset}", output_file=out_file, write_data=f"{write_data}", read_data=f"{read_data}", ranks_per_node=f"{ranks_per_node}", write_output=1)
                            with open(f"{command_log_dir}/mdtest_command_{node_type}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank_timed", 'a') as file:
                                file.write(f"The following is the mdtest command")
                                tmp_cmd_string = ""
                                for cmd_el in mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"].command:
                                    tmp_cmd_string += f" {cmd_el}"
                                file.write(tmp_cmd_string)
                            
                            mdtest_obj_dict[f"{node_type}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"].run()
                            old_elapsed_time = elapsed_time
                            start_time, end_time, elapsed_time = benchmark_tools.mdtest_start_end_elapsed_time(out_file)

                            print (f"entered the optimizer. Old elapsed time: {old_elapsed_time}, New elapsed time: {elapsed_time}, old files_per_rank {files_per_rank}, new files per rank {new_files_per_rank}, multiple is: {multiple}")
                            files_per_rank = new_files_per_rank
                    total_files_optimized = files_per_rank * tmp_rank
                print(f"mdtest job {node_type}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank is finished. [s-{start_time}], [e-{end_time}], elapsed time: {elapsed_time}")
                
                sys.stdout.flush()
