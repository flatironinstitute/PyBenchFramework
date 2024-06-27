import os
import handler_class
from datetime import datetime
import sys
import benchmark_tools
import args_handler
import miscellaneous

'''
var_name = "PyBench_root_dir"

try:
    PyBench_root_dir = os.environ[var_name]
    print(f"{var_name} = {PyBench_root_dir}")
except KeyError:
    print(f"{var_name} is not set, please set the root directory before running this script.")
    sys.exit(1)
'''

#args = args_handler.handle_arguments()

def server_fio(args, PyBench_root_dir):
    job_number = args['slurm_job_number']

    # Count the number of lines in the job hosts file
    line_count = benchmark_tools.count_lines(args['hosts_file'])

    current_dir = os.getcwd()

    fio_ob_dict = {}
    fio_out_dict = {}

    proc = benchmark_tools.split_arg_sequence(args['job_number'], '--job-number') 
    nodes = benchmark_tools.split_arg_sequence(str(args['node_count']), '--node-count')
    files = nodes.copy()

    set_noscrub = args['no_scrub']

    if args['split_hosts_file']:
        benchmark_tools.create_node_list(args['node_count'], args['hosts_file'], PyBench_root_dir, job_number)

    config_template_path = args['template_path']

    with open(config_template_path, 'r') as file:
        original_file_contents = file.read()

    fio_scrub = handler_class.FIOTool()

    if set_noscrub == 1:
        fio_scrub.set_noscrub()

    log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"

    miscellaneous.ensure_log_directory_exists(log_dir,1)
    miscellaneous.ensure_log_directory_exists(command_log_dir,1)

    for node_count in nodes:

        for job_count in proc:
            
            file_count = job_count

            # Reset file_contents to the original template for each iteration
            file_contents = original_file_contents
            file_contents = file_contents.replace("__block_size__", args['block_size'])
            file_contents = file_contents.replace("__number_of_jobs__", f"{job_count}")
            file_contents = file_contents.replace("__dir_var__", args['directory'])
            file_contents = file_contents.replace("__io_type_var__", args['io_type'])
            file_contents = file_contents.replace("__time_var__",f"{args['time']}")
            
            with open(f"examples/test_files/multinode_{job_count}p_{file_count}f_{args['block_size']}_{args['io_type']}.fio", 'w') as file:
                file.write(file_contents)

            fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"] = handler_class.FIOTool()
            
            fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"].setup_command(config_file=f"{PyBench_root_dir}/examples/test_files/multinode_{job_count}p_{file_count}f_{args['block_size']}_{args['io_type']}.fio", output_format="json", output_file=f"{log_dir}/{node_count}n_{job_count}p_{file_count}f_{args['block_size']}.json", host_file=f"{PyBench_root_dir}/host_files/{job_number}_{node_count}_hosts.file")
            
            with open(f"{command_log_dir}/{job_number}_{node_count}n_{job_count}p_{file_count}f_{args['platform_type']}_command", 'a') as file:
                file.write(f"num nodes is {node_count}, job number is {job_count}")
                tmp_cmd_string = ""
                for cmd_el in fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"].command:
                    tmp_cmd_string += f" {cmd_el}"
                file.write(tmp_cmd_string)
            
            fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"].run()
            
            print(f"Job num: {job_count}, node count: {node_count}. Iteration is finished.")
            sys.stdout.flush()

    if set_noscrub == 1:
        fio_scrub.set_scrub()

