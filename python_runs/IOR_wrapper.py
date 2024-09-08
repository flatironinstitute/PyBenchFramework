import os
import socket
import handler_class
from datetime import datetime
import json
import sys
import benchmark_tools
import args_handler
import miscellaneous
import network_collect 
import threading
import time
import re
import shutil

def wrap_IOR(args, PyBench_root_dir):

    job_number = args['slurm_job_number']

    current_dir = os.getcwd()

    mdtest_obj_dict = {}
    #handler_class.mdtestTool()

    log_dir = f"{PyBench_root_dir}/results/iortest/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    tmp_log_dir = f"{log_dir}/tmp_files"
    
    hostname = socket.gethostname()

    mpi_ranks = list(benchmark_tools.split_arg_sequence(args['mpi_ranks'], "--mpi-ranks"))
    filename = args['testFile']
    node_count = list(benchmark_tools.split_arg_sequence(args['node_count'], "--node-count"))
    block_size = args['block_size']
    transfer_size = args['transfer_size']
    segment_count = args['segment_count']
    reorder_tasks = args['reorder_tasks']
    fsync = args['fsync']
    #if 'output_file' in args.keys():
    #    output_file = args['output_file']
    if 'output_format' in args.keys():
        output_format = args['output_format']
    if 'deadline_for_stonewalling' in args.keys():
        deadline_for_stonewalling = args['deadline_for_stonewalling']
    else:
        deadline_for_stonewalling = 0
    

    #total_ranks = mpi_ranks[0]*node_count[0]

    #output_file = f"{log_dir}/ranks_per_node_{mpi_ranks[0]}_node_count_{node_count[0]}"
    io_type = args['io_type']
    if 'use_existing_file' in args.keys():
        use_existing_file=args['use_existing_file']
    else:
        use_existing_file = False

    if 'job_note' in args.keys():
        with open(f"{log_dir}/job_note.txt", 'w') as file:
            file.write(args['job_note'])

    ior_obj_dict = {}

    print (f"SEQUENCES ARE {mpi_ranks} and nodes {node_count}")
    for nodes in node_count:
        for ranks in mpi_ranks:
            print (f"BEGINNING OF LOOPS _---------------------- {ranks} and nodes {nodes}")
            if 'unit_restart' in args:
                if args['unit_restart'] == 1:
                    pattern = '/'
                    split_dir = re.split(pattern, filename)
                    cephtest_root = '/'+split_dir[1]+'/'+split_dir[2]
                    miscellaneous.restart_ceph_unit(cephtest_root)
            
            total_ranks = ranks * nodes
            output_file = f"{log_dir}/ranks_per_node_{ranks}_node_count_{nodes}"

            ior_obj_dict[f"{ranks}_{nodes}"] = handler_class.newIORTool()
            ior_obj_dict[f"{ranks}_{nodes}"].setup_command(config_file=f"{PyBench_root_dir}/{args['config']}",mpi_ranks=total_ranks,filename=filename,ranks_per_node=ranks,block_size=block_size,transfer_size=transfer_size,segment_count=segment_count,reorder_tasks=1,fsync=1,output_file=f"{output_file}",output_format=output_format, deadline_for_stonewalling=deadline_for_stonewalling,io_type=io_type,use_existing_file=use_existing_file)

            with open(f"{command_log_dir}/command_ior_{ranks}_{nodes}", 'w') as file:
                file.write(f"The following is the ior command")
                tmp_cmd_string = ""
                for cmd_el in ior_obj_dict[f"{ranks}_{nodes}"].command:
                    tmp_cmd_string += f" {cmd_el}"
                file.write(tmp_cmd_string)
    
            ior_obj_dict[f"{ranks}_{nodes}"].run()

    for nodes in node_count:
        for ranks in mpi_ranks:
            #Output handling
            output_file = f"{log_dir}/ranks_per_node_{ranks}_node_count_{nodes}"
            combined_json_log_file = f"{log_dir}/combined_{ranks}_{nodes}_{block_size}"
            json_log_file = output_file 

            if os.path.exists(json_log_file):
                bw, iops = miscellaneous.load_ior_json_results(json_log_file, log_dir)
            else:
                print( f"JSON LOG FILE NOT FOUND! ------- {output_file}" )
                sys.exit()

            data = {
                    "nodes": nodes,
                    "processors": ranks,
                    "bw": bw,
                    "iops": iops
            }

            with open(combined_json_log_file, 'w') as json_file:
                json.dump(data, json_file, indent=4)
                print(f"Data successfully written to {combined_json_log_file}")

