import os
import sys
import miscellaneous
from args_handler import handle_arguments

def prep_work(args, PyBench_root_dir):
    job_number = args['slurm_job_number']

    #log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    if args['benchmark'] == "newIORTool" or args['benchmark'] == "testIORTool":
        log_dir = f"{PyBench_root_dir}/results/iortest/{args['io_type']}/{args['platform_type']}/{job_number}"
    if args['benchmark'] == "testmdtest":
        log_dir = f"{PyBench_root_dir}/results/{args['not_taken_into_account']['io_type']}/{args['not_taken_into_account']['platform_type']}/{job_number}"
    else:
        log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    
    command_log_dir = f"{log_dir}/commands"
    network_log_dir = f"{PyBench_root_dir}/network_stats/{job_number}"
    test_files_log = f"{PyBench_root_dir}/examples/test_files"
    tmp_log_dir = f"{log_dir}/tmp_files"

    miscellaneous.ensure_log_directory_exists(log_dir,1)
    miscellaneous.ensure_log_directory_exists(command_log_dir,1)
    miscellaneous.ensure_log_directory_exists(network_log_dir, 1)
    miscellaneous.ensure_log_directory_exists(test_files_log, 1)
    miscellaneous.ensure_log_directory_exists(tmp_log_dir, 1)

    try:
        with open(f"{log_dir}/hostname_mapping.txt", "x") as file:
            #file.write("Hostname_mapping file was created because it did not exist.\n")
            pass
    except FileExistsError:
        print("File already exists.")

var_name = "PyBench_root_dir"

try:
    PyBench_root_dir = os.environ[var_name]
    #print(f"{var_name} = {PyBench_root_dir}")
except KeyError:
    print(f"{var_name} is not set, please set the root directory before running this script.")
    sys.exit(1)

args = handle_arguments()
prep_work(args, PyBench_root_dir)
