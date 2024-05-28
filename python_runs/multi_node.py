import os
import handler_class
from datetime import datetime
import sys
import benchmark_tools
import args_handler
import miscellaneous


root_dir = "/mnt/home/skrit/Documents/benchmark_handler"
args = args_handler.handle_arguments()

job_number = args['slurm_job_number']

# Process the argument
print(f"Received slurm job number: {job_number}")

host_filename = f"{root_dir}/host_files/{job_number}_hosts.file"

# Count the number of lines in the job hosts file
line_count = benchmark_tools.count_lines(host_filename)
print(f"Line count is: {line_count}")

current_dir = os.getcwd()
#fio = handler_class.FIOTool()

fio_ob_dict = {}
fio_out_dict = {}

i=10
j=10
proc = [25, 20, 15, 10] 
files = [25, 20, 15, 10]
nodes = [10, 8, 6, 4, 2, 1]
set_noscrub = 0

if (args['split_file'] == "True"):
    benchmark_tools.create_node_list(nodes, host_filename, root_dir, job_number)

config_template_path = f"{root_dir}/examples/template/template.fio"
#old_proc = proc[0]
#old_files = files[0]
#old_nodes = nodes[0]

fio_scrub = handler_class.FIOTool()


if set_noscrub == 0:
    fio_scrub.set_noscrub()
    set_noscrub = 1

log_dir = f"{root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"

miscellaneous.ensure_log_directory_exists(log_dir,1)

for node_count in nodes:

    with open(config_template_path, 'r') as file:
        file_contents = file.read()

    for job_count in proc:
        
        file_count = job_count

        #{'slurm_job_number': 3442430, 'block_size': '1M', 'directory': '/mnt/home/skrit/Documents/benchmark_handler/examples/template', 'job_number': None, 'time': 300, 'io_type': 'randwrite'}
        
        file_contents = file_contents.replace("__block_size__", args['block_size'])
        file_contents = file_contents.replace("__number_of_jobs__", str(job_count))
        file_contents = file_contents.replace("__dir_var__", args['directory'])
        file_contents = file_contents.replace("__io_type_var__", args['io_type'])
        
        with open(f"examples/test_files/multinode_{job_count}p_{file_count}f_{args['block_size']}_{args['io_type']}.fio", 'w') as file:
            file.write(file_contents)

        
        fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"] = handler_class.FIOTool()
        
        fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"].setup_command(config_file=f"{root_dir}/examples/test_files/multinode_{job_count}p_{file_count}f_{args['block_size']}_{args['io_type']}.fio", output_format="json", output_file=f"{log_dir}/{node_count}n_{job_count}p_{file_count}f_{args['block_size']}.json", host_file=f"{root_dir}/host_files/{job_number}_{node_count}_hosts.file")
        
        with open(f"{root_dir}/results/{args['io_type']}/{args['platform_type']}/commands/{job_number}_{node_count}n_{job_count}p_{file_count}f_{args['platform_type']}_command", 'a') as file:
            file.write(f"num nodes is {node_count}")
            tmp_cmd_string = ""
            for cmd_el in fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"].command:
                tmp_cmd_string += f" {cmd_el}"
            file.write(tmp_cmd_string)
        
        fio_ob_dict[f"{node_count}n_{job_count}p_{file_count}f_{args['io_type']}"].run()
        
        print(f"Job num: {job_count}, node count: {node_count}. Iteration is finished.")

if set_noscrub == 1:
    fio_scrub.set_scrub()

