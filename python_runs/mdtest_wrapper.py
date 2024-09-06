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

    for node in node_count:
        for rank in mpi_ranks:
            tmp_rank = int(rank)
            node_type = int(node)
            tmp_rank = node_type * tmp_rank
            for files_per_rank in files_per_rank_list:
                if total_files_optimized != 0:
                    files_per_rank = total_files_optimized / tmp_rank

                out_file = f"{log_dir}/mdtest_output_{node_type}_nodes_{tmp_rank}_ranks_{files_per_rank}_files_per_rank"

                print (f"ranks are {tmp_rank} and type is {type(tmp_rank)}, nodes are {node_type} and type is {type(node_type)}")
                mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{files_per_rank}_files_per_rank"] = handler_class.mdtestTool()

                mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{files_per_rank}_files_per_rank"].setup_command(config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{files_per_rank}", test_repetition=f"{test_repetition}", directory=f"{directory}", offset=f"{offset}", output_file=out_file, write_data=f"{write_data}", read_data=f"{read_data}", node_count=f"{node_type}")
            
                with open(f"{command_log_dir}/mdtest_command_{node_type}_nodes_{tmp_rank}_ranks_{files_per_rank}_files_per_rank", 'a') as file:
                    file.write(f"The following is the mdtest command")
                    tmp_cmd_string = ""
                    for cmd_el in mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{files_per_rank}_files_per_rank"].command:
                        tmp_cmd_string += f" {cmd_el}"
                    file.write(tmp_cmd_string)
                
                mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{files_per_rank}_files_per_rank"].run()
                
                start_time, end_time, elapsed_time = benchmark_tools.mdtest_start_end_elapsed_time(out_file)
                
                if elapsed_time <= 59 or elapsed_time >= 90:
                    while elapsed_time <= 59 or elapsed_time >= 90:
                        source = out_file
                        tmp_log_filename = re.split('/', out_file)[len(re.split('/', out_file)) - 1]
                        destination = f"{tmp_log_dir}/{tmp_log_filename}"
                        shutil.move(source, destination)
                        
                        multiple = 60 / elapsed_time
                        if elapsed_time <= 59:
                            new_files_per_rank = int(files_per_rank * multiple) + int(0.05 * files_per_rank)
                        if elapsed_time >= 90:
                            new_files_per_rank = int(files_per_rank * multiple) - int(0.05 * files_per_rank)

                        out_file = f"{log_dir}/mdtest_output_{node_type}_nodes_{tmp_rank}_ranks_{new_files_per_rank}_new_files_per_rank_timed"
                        
                        mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{new_files_per_rank}_new_files_per_rank"] = handler_class.mdtestTool()
                        mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{new_files_per_rank}_new_files_per_rank"].setup_command(config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{new_files_per_rank}", test_repetition=f"{test_repetition}", directory=f"{directory}", offset=f"{offset}", output_file=out_file, write_data=f"{write_data}", read_data=f"{read_data}", node_count=f"{node_type}")
                        with open(f"{command_log_dir}/mdtest_command_{node_type}_nodes_{tmp_rank}_ranks_{new_files_per_rank}_new_files_per_rank_timed", 'a') as file:
                            file.write(f"The following is the mdtest command")
                            tmp_cmd_string = ""
                            for cmd_el in mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{new_files_per_rank}_new_files_per_rank"].command:
                                tmp_cmd_string += f" {cmd_el}"
                            file.write(tmp_cmd_string)
                        
                        mdtest_obj_dict[f"{node_type}_nodes_{tmp_rank}_ranks_{new_files_per_rank}_new_files_per_rank"].run()
                        old_elapsed_time = elapsed_time
                        start_time, end_time, elapsed_time = benchmark_tools.mdtest_start_end_elapsed_time(out_file)

                        print (f"entered the optimizer. Old elapsed time: {old_elapsed_time}, New elapsed time: {elapsed_time}, old files_per_rank {files_per_rank}, new files per rank {new_files_per_rank}, multiple is: {multiple}")
                        files_per_rank = new_files_per_rank
                total_files_optimized = files_per_rank * tmp_rank
                print(f"mdtest job {node_type}_nodes_{tmp_rank}_ranks_{files_per_rank}_files_per_rank is finished. [s-{start_time}], [e-{end_time}], elapsed time: {elapsed_time}")
                
                sys.stdout.flush()
