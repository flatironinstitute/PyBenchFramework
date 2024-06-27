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

'''
var_name = "PyBench_root_dir"

try:
    PyBench_root_dir = os.environ[var_name]
    print(f"{var_name} = {PyBench_root_dir}")
except KeyError:
    print(f"{var_name} is not set, please set the root directory before running this script.")
    sys.exit(1)
'''

def serverless_fio(args, PyBench_root_dir):
    def background_network_monitor():
            print("network_monitoring")
            network_counter_collection.monitor_traffic(args)

    job_number = args['slurm_job_number']

    current_dir = os.getcwd()

    fio_ob_dict = {}
    fio_out_dict = {}

    proc = list(benchmark_tools.split_arg_sequence(args['job_number'], '--job-number')) 

    config_template_path = args['template_path']

    with open(config_template_path, 'r') as file:
        original_file_contents = file.read()

    log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    
    hostname = socket.gethostname()
    '''
    if hostname == args["first_node"]:
        miscellaneous.ensure_log_directory_exists(log_dir,1)
        miscellaneous.ensure_log_directory_exists(command_log_dir,1)
    
    
    time.sleep(10)
    '''

    for job_count in proc:
        
        file_count = job_count

        # Reset file_contents to the original template for each iteration
        file_contents = original_file_contents
        file_contents = file_contents.replace("__block_size__", args['block_size'])
        file_contents = file_contents.replace("__number_of_jobs__", f"{job_count}")
        file_contents = file_contents.replace("__dir_var__", args['directory'])
        file_contents = file_contents.replace("__io_type_var__", args['io_type'])
        file_contents = file_contents.replace("__time_var__",f"{args['time']}")
        
        with open(f"examples/test_files/{job_number}_{hostname}_{job_count}p_{file_count}f_{args['block_size']}_{args['io_type']}.fio", 'w') as file:
            file.write(file_contents)

        fio_ob_dict[f"{hostname}_{job_count}p_{file_count}f_{args['io_type']}"] = handler_class.FIOTool()
        
        fio_ob_dict[f"{hostname}_{job_count}p_{file_count}f_{args['io_type']}"].setup_command(config_file=f"{PyBench_root_dir}/examples/test_files/{job_number}_{hostname}_{job_count}p_{file_count}f_{args['block_size']}_{args['io_type']}.fio", output_format="json", output_file=f"{log_dir}/{hostname}_{job_count}p_{file_count}f_{args['block_size']}.json") #, host_file=f"{PyBench_root_dir}/host_files/{job_number}_{node_count}_hosts.file")
        
        with open(f"{command_log_dir}/{job_number}_{hostname}_{job_count}p_{file_count}f_{args['platform_type']}_command", 'a') as file:
            file.write(f"num nodes is 1, job number is {job_count}")
            tmp_cmd_string = ""
            for cmd_el in fio_ob_dict[f"{hostname}_{job_count}p_{file_count}f_{args['io_type']}"].command:
                tmp_cmd_string += f" {cmd_el}"
            file.write(tmp_cmd_string)
        
        network_counter_collection.stop_thread = False
        background_thread = threading.Thread(target=background_network_monitor)
        background_thread.start()
        start_time = time.time()
        fio_ob_dict[f"{hostname}_{job_count}p_{file_count}f_{args['io_type']}"].run()
        network_counter_collection.stop_thread = True
        end_time = time.time()

        background_thread.join()

        elapsed_time = end_time - start_time
        print(f"Job num: {job_count}, node count: 1. Iteration is finished. {hostname} [s-{start_time}], [e-{end_time}]")
        
        sys.stdout.flush()

    stop_thread = True
