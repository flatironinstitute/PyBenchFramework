import os
import socket
import handler_class
from datetime import datetime
import json
import sys
import yaml
import benchmark_tools
import args_handler
import miscellaneous
import network_collect 
import threading
import time
import re
import shutil

def test_wrap_IOR(args, PyBench_root_dir):

    job_number = args['slurm_job_number']

    current_dir = os.getcwd()

    mdtest_obj_dict = {}
    #handler_class.mdtestTool()

    log_dir = f"{PyBench_root_dir}/results/iortest/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    tmp_log_dir = f"{log_dir}/tmp_files"
    
    hostname = socket.gethostname()

    required_args = ['config','mpi_ranks', 'node_count', 'blockSize', 'filename', 'transferSize', 'segmentCount']
    for i in required_args:
        if i not in args:
            arg_string = i.replace('_','-')
            print(f"Missing option --{arg_string}. Please look at IOR and/or MPI documentation and fix this error.")
            sys.exit()
        elif not args[i]:
            arg_string = i.replace('_','-')
            print(f"Incorrect --{arg_string} usage. Please look at IOR and/or MPI documentation and fix this error.")
            sys.exit()

    print("Required arguments seem valid...")

    config_file = args['config']
    print(config_file)

    if config_file:
        try:
            with open (config_file, 'r') as opts_file:
                config = yaml.safe_load(opts_file)
        except yaml.YAMLError as e:
            print(f"Error loading YAML file: {e}")
        except FileNotFoundError as e:
            print(f"File not found: {e}")
        except Exception as e:
            print(f"An unexpected error has occurred: {e}")
    else:
        raise ValueError("Configuration file must be specified. IOR...")

    for key,value in config.items():
        if key != "config_options" and key != "command_extensions":
            print(f"{key}: {value}")
        if key == "config_options":
            print("Configuration options:")
            for key,value in config["config_options"].items():
                print (f"{key}: {value}")
        if key == "command_extensions":
            print("Command extensions:")
            for i in config["command_extensions"]:
                print(f"{i}")

    if 'job_note' in args.keys():
        with open(f"{log_dir}/job_note.txt", 'w') as file:
            file.write(args['job_note'])

    mpi_ranks = list(benchmark_tools.split_arg_sequence(args['mpi_ranks'], "--mpi-ranks"))
    filename = args['filename']
    node_count = list(benchmark_tools.split_arg_sequence(args['node_count'], "--node-count"))
    block_size = args['blockSize']
    transfer_size = args['transferSize']
    segment_count = args['segmentCount']
    ior_obj_dict = {}
    
    print (f"SEQUENCES ARE {mpi_ranks} and nodes {node_count}")
    for nodes in node_count:
        for ranks in mpi_ranks:
            print (f"BEGINNING OF LOOPS ---------------------- ranks per node: {ranks} and nodes: {nodes}")

            if 'unit_restart' in args:
                if args['unit_restart'] == 1:
                    pattern = '/'
                    split_dir = re.split(pattern, filename)
                    cephtest_root = '/'+split_dir[1]+'/'+split_dir[2]
                    miscellaneous.restart_ceph_unit(cephtest_root)
            
            total_ranks = ranks * nodes
            print(f"TOTAL RANKS ARE {total_ranks}")
            output_file = f"{log_dir}/ranks_per_node_{ranks}_node_count_{nodes}"
            
            ior_obj_dict[f"{ranks}_{nodes}"] = handler_class.test_ior_tool()
            ior_obj_dict[f"{ranks}_{nodes}"].setup_command(config=config, mpi_ranks=total_ranks,ranks_per_node=ranks,output_file=output_file)
            
            with open(f"{command_log_dir}/command_ior_{ranks}_{nodes}", 'w') as file:
                tmp_cmd_string = ""
                for cmd_el in ior_obj_dict[f"{ranks}_{nodes}"].command:
                    tmp_cmd_string += f" {cmd_el}"
                file.write(tmp_cmd_string)
            
            ior_obj_dict[f"{ranks}_{nodes}"].run()

    '''
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
    '''
