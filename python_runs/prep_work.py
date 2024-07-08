import os
import sys
import miscellaneous
from args_handler import handle_arguments

def prep_work(args, PyBench_root_dir):
    job_number = args['slurm_job_number']

    log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    network_log_dir = f"{PyBench_root_dir}/network_stats/{job_number}"

    miscellaneous.ensure_log_directory_exists(log_dir,1)
    miscellaneous.ensure_log_directory_exists(command_log_dir,1)
    miscellaneous.ensure_log_directory_exists(network_log_dir, 1)

var_name = "PyBench_root_dir"

try:
    PyBench_root_dir = os.environ[var_name]
    print(f"{var_name} = {PyBench_root_dir}")
except KeyError:
    print(f"{var_name} is not set, please set the root directory before running this script.")
    sys.exit(1)

args = handle_arguments()
prep_work(args, PyBench_root_dir)
