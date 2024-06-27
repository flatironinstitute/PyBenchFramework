import os
import socket
import handler_class
from datetime import datetime
import sys
import benchmark_tools
import args_handler
import miscellaneous
import network_counter_collection 
import threading
import time

def wrap_mdtest(args, PyBench_root_dir):

    job_number = args['slurm_job_number']

    current_dir = os.getcwd()

    mdtest_obj = handler_class.mdtestTool()

    log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    
    hostname = socket.gethostname()

    mpi_ranks = args['mpi_ranks']
    files_per_rank = args['files_per_rank']
    test_repetition = args['test_repetition']
    directory = args['directory']

    mdtest_obj.setup_command(config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{mpi_ranks}", files_per_rank=f"{files_per_rank}", test_repetition=f"{test_repetition}", directory=f"{directory}", output_file=f"{log_dir}/mdtest_output")
        
    with open(f"{command_log_dir}/mdtest_command", 'a') as file:
        file.write(f"The following is the mdtest command")
        tmp_cmd_string = ""
        for cmd_el in mdtest_obj.command:
            tmp_cmd_string += f" {cmd_el}"
        file.write(tmp_cmd_string)
    
    start_time = time.time()
    mdtest_obj.run()
    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"mdtest job is finished. [s-{start_time}], [e-{end_time}]")
    
    sys.stdout.flush()
