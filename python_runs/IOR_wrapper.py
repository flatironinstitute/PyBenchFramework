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

def wrap_IOR(args, PyBench_root_dir):
    '''
    mpi_ranks = params.get('mpi_ranks')
    filename = params.get('testFile')
    node_count = params.get('node_count')
    block_size = params.get('block_size')
    transfer_size = params.get('transfer_size')
    segment_count = params.get('segment_count')
    reorder_tasks = params.get('reorder_tasks')
    fsync = params.get('fsync')
    output_file = params.get('output_file')
    output_format = params.get('output_format')
    '''

    job_number = args['slurm_job_number']

    current_dir = os.getcwd()

    mdtest_obj_dict = {}
    #handler_class.mdtestTool()

    log_dir = f"{PyBench_root_dir}/results/{args['io_type']}/{args['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    tmp_log_dir = f"{log_dir}/tmp_files"
    
    hostname = socket.gethostname()

    mpi_ranks = benchmark_tools.split_arg_sequence(args['mpi_ranks'], "--mpi-ranks")
    filename = args['testFile']
    node_count = benchmark_tools.split_arg_sequence(args['node_count'], "--node-count")
    block_size = args['block_size']
    transfer_size = args['transfer_size']
    segment_count = args['segment_count']
    reorder_tasks = args['reorder_tasks']
    fsync = args['fsync']
    if 'output_file' in args.keys():
        output_file = args['output_file']
    if 'output_format' in args.keys():
        output_format = args['output_format']
    if 'deadline_for_stonewalling' in args.keys():
        deadline_for_stonewalling = args['deadline_for_stonewalling']
    

    total_ranks = mpi_ranks[0]*node_count[0]

    ior_obj = handler_class.newIORTool()
    ior_obj.setup_command(config_file=f"{PyBench_root_dir}/{args['config']}",mpi_ranks=total_ranks,filename=args['testFile'],ranks_per_node=mpi_ranks[0],block_size=block_size,transfer_size=transfer_size,segment_count=segment_count,reorder_tasks=1,fsync=1,output_file=f"{log_dir}/{output_file}",output_format=output_format, deadline_for_stonewalling=deadline_for_stonewalling)

    with open(f"{command_log_dir}/ior_command", 'a') as file:
        file.write(f"The following is the ior command")
        tmp_cmd_string = ""
        for cmd_el in ior_obj.command:
            tmp_cmd_string += f" {cmd_el}"
        file.write(tmp_cmd_string)
    
    ior_obj.run()
