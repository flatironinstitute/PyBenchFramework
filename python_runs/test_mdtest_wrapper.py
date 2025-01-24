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
import subprocess
from datetime import datetime

def test_wrap_mdtest(args, PyBench_root_dir):

    job_number = args['slurm_job_number']

    current_dir = os.getcwd()

    mdtest_obj_dict = {}
    #handler_class.mdtestTool()

    log_dir = f"{PyBench_root_dir}/results/{args['not_taken_into_account']['io_type']}/{args['not_taken_into_account']['platform_type']}/{job_number}"
    command_log_dir = f"{log_dir}/commands"
    tmp_log_dir = f"{log_dir}/tmp_files"
    
    hostname = socket.gethostname()

    mpi_ranks = sorted(benchmark_tools.split_arg_sequence(args['general_opts']['mpi_ranks'], "--mpi-ranks"))
    files_per_rank_list = sorted(benchmark_tools.split_arg_sequence(args['mdtest_opts']['files_per_rank'], "--files-per-rank"))
    #test_repetition = args['test_repetition']
    directory = args['mdtest_opts']['directory']
    #offset = args['offset']
    #write_data = args['write_data']
    #read_data = args['read_data']
    node_count = sorted(benchmark_tools.split_arg_sequence(args['general_opts']['node_count'], "--node-count"))

    
    #config_file = args['config']
    #config = miscellaneous.get_config_params(config_file)

    total_files_optimized = 0
    if args['not_taken_into_account']['timed']:
        times = sorted(benchmark_tools.split_arg_sequence(args['not_taken_into_account']['timed'], "--timed"))
        if len(times) != 2:
            print ( f"{datetime.now().strftime('%b %d %H:%M:%S')} When using the 'timed' option, please ensure to specify two comma-delimited integer values indicating a lower threshold and upper threshold of time in seconds that the test should run for. Values as interpreted are: {times}" )
            sys.exit()
        lower_time_threshold = times[0]
        upper_time_threshold = times[1]


    if 'job_note' in args['not_taken_into_account'].keys():
        job_note = f"{args['not_taken_into_account']['job_note']}"
        with open(f"{log_dir}/job_note.txt", 'w') as file:
            file.write(job_note)
    else:
        print("{datetime.now().strftime('%b %d %H:%M:%S')} Job note required for job tracking. Please include an argument under the \"not_taken_into_account\" YAML dict")
        sys.exit()
    
    #If the "--in-parts" argument is used, we will break out into a separate a logical branch. This new branch may become the main branch and the old logic may take the place of the current logic. Whatever parts of the old code that can be recycled, should be?
    if "not_taken_into_account" in args.keys():
        print("in not_taken_into_account")
        if "in_parts" in args["not_taken_into_account"].keys():
            if args["not_taken_into_account"]["in_parts"]:
                print("in in_parts")
                #for each iteratable element in  general_opts and mdtest_opts I want a counter, a way to iterate over it (so maybe a key), and the sub-elements. EXCEPT command-extensions:
                result_dict = {}
                combined_opts = {**args["general_opts"],**args["mdtest_opts"]}
                
                for key, value in combined_opts.items():
                    if isinstance(value, str) and ',' in value:  # Handle comma-separated strings
                        value_list = list(value.split(','))
                    else:  # Handle single values or non-comma-separated strings
                        value_list = [value]
                    if key == "command_extensions":
                        pass
                    
                    result_dict[key] = {key:value_list, 'counter': len(value_list) - 1, 'tmp_counter': len(value_list) - 1}

                entered_loop = 0
                for node in result_dict['node_count']['node_count']:
                    for rank in result_dict['mpi_ranks']['mpi_ranks']:
                        tmp_rank = int(rank)
                        tmp_node = int(node)
                        tmp_rank = tmp_node * tmp_rank
                        ranks_per_node = int(tmp_rank / tmp_node)

                        universal_key_counter = 1 
                        for key, value in result_dict.items():
                            value['tmp_counter'] = value['counter']
                        
                        files_per_rank = int(int(result_dict['files_per_rank']['files_per_rank'][result_dict['files_per_rank']['tmp_counter']]) / int(tmp_rank))
                        entered_loop = 1
                        while universal_key_counter != 0:
                            universal_key_counter = 0
                            tmp_result_dict = {}
                            for command_extent_element in reversed(result_dict['command_extensions']['command_extensions']):
                                if 'unit_restart' in args['not_taken_into_account'].keys():
                                    if args['not_taken_into_account']['unit_restart'] == 1:
                                        pattern = '/'
                                        split_dir = re.split(pattern, directory)
                                        FS_root = '/'+split_dir[1]+'/'+split_dir[2]
                                        miscellaneous.restart_ceph_unit(FS_root)

                                #Set temporary values for the current loop and the output file
                                for key2,value2 in result_dict.items():
                                    if key2 == "command_extensions":
                                        tmp_result_dict["command_extensions"] = command_extent_element
                                    else:
                                        tmp_result_dict[f"{key2}"] = value2[f"{key2}"][value2['tmp_counter']]

                                config = {**tmp_result_dict,**args["not_taken_into_account"]}

                                out_file = f"{log_dir}/mdtest_output_{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"
                                #Print statistics
                                print (f"{datetime.now().strftime('%b %d %H:%M:%S')} ranks per node are {ranks_per_node}, nodes are {tmp_node}, and mdtest job type is {command_extent_element}")
                                #---------
                                
                                #Create mdtest object
                                mdtest_obj_dict[f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"] = handler_class.mdtestTool()
                                mdtest_obj_dict[f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].setup_command(config=config, config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{files_per_rank}", directory=f"{directory}", output_file=out_file, ranks_per_node=f"{ranks_per_node}", write_output=args['mdtest_opts']['write_output'])

                                #Write command into command output file
                                with open(f"{command_log_dir}/mdtest_{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank", 'a') as file:
                                    file.write(f"The following is the mdtest command")
                                    tmp_cmd_string = ""
                                    for cmd_el in mdtest_obj_dict[f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].command:
                                        tmp_cmd_string += f" {cmd_el}"
                                    file.write(tmp_cmd_string)
                                #---------

                                #Run mdtest through object and enter optimizer as necessary
                                mdtest_obj_dict[f"{command_extent_element}_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].run()
                                
                                #create/delete snapshots
                                '''
                                if command_extent_element == "YuC":
                                    if not os.path.exists(f"{directory}/.snap/test_snapshots"):
                                        result = subprocess.run(f"mkdir {directory}/.snap/test_snapshots", shell=True, capture_output=False, text=True, check=True)
                                        print("{datetime.now().strftime('%b %d %H:%M:%S')} Creating snapshot after running creation mdtest...")
                                    else:
                                        print("{datetime.now().strftime('%b %d %H:%M:%S')} snapshot already exists, something went wrong")

                                if command_extent_element == "Yur":
                                    if os.path.exists(f"{directory}/.snap/test_snapshots"):
                                        print("{datetime.now().strftime('%b %d %H:%M:%S')} Deleting snapshot after running deletion mdtest...")
                                        result = subprocess.run(f"rmdir {directory}/.snap/test_snapshots", shell=True, capture_output=False, text=True, check=True)
                                    else:
                                        print("{datetime.now().strftime('%b %d %H:%M:%S')} snapshot doesn't exist, something went wrong.")
                                '''
                                #--------

                            # Iterate through arguments that have still not been used, decrement temporary counters
                            for key, value in result_dict.items():

                                if key != 'mpi_ranks' and key != 'node_count' and key != 'write_output' and key != "command_extensions":
                                    if value['tmp_counter'] == 0:
                                        pass
                                    else:
                                        value['tmp_counter'] = value['tmp_counter'] - 1
                                        universal_key_counter = 1
                            #----------
            else:
                print("not in_parts")
                sys.exit()
            '''
                for node in result_dict['node_count']['node_count']:
                    for rank in result_dict['mpi_ranks']['mpi_ranks']:
                        universal_key_counter = 1 
                        for key, value in result_dict.items():
                            value['tmp_counter'] = value['counter']
                        while universal_key_counter != 0:
                            universal_key_counter = 0
                            final_command = f"mpirun -n {rank} --map-by node -N {node} --verbose mdtest"
                            for key, value in result_dict.items():
                                if key != 'mpi_ranks' and key != 'node_count' and key != 'write_output':
                                    if value['tmp_counter'] == 0:
                                        if key in key_map:
                                            final_command += f" -{key_map[key]} {str(value[key][0])}"
                                        else:
                                            final_command += f" -{key} {str(value[key][0])}"
                                    else:
                                        if key in key_map:
                                            final_command += f" -{key_map[key]} {str(value[key][value['tmp_counter']])}"
                                        else:
                                            final_command += f" -{key} {str(value[key][value['tmp_counter']])}"
                                        value['tmp_counter'] = value['tmp_counter'] - 1
                                        universal_key_counter = 1
                                #if key == 'command_extensions'
                                #    final_command += f" -{str(value[key][value['counter']])}"
                            print(final_command)
            '''
    else:
        print("General ops which are not yet taken into account are required.")
        sys.exit()
    sys.exit()
    for node in node_count:
        for rank in mpi_ranks:
            tmp_rank = int(rank)
            tmp_node = int(node)
            tmp_rank = tmp_node * tmp_rank
            ranks_per_node = int(tmp_rank / tmp_node)
            for files_per_rank in files_per_rank_list:

                if 'unit_restart' in args:
                    if args['unit_restart'] == 1:
                        pattern = '/'
                        split_dir = re.split(pattern, directory)
                        FS_root = '/'+split_dir[1]+'/'+split_dir[2]
                        miscellaneous.restart_ceph_unit(FS_root)

                if total_files_optimized != 0:
                    files_per_rank = total_files_optimized / tmp_rank

                if files_per_rank < 10:
                    files_per_rank = 10
                #elif files_per_rank > 10000:
                #    files_per_rank = 10000
                out_file = f"{log_dir}/mdtest_output_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"

                print (f"ranks per node are {ranks_per_node} and type is {type(ranks_per_node)}, nodes are {tmp_node} and type is {type(tmp_node)}")
                mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"] = handler_class.mdtestTool()

                mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].setup_command(config=config, config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{files_per_rank}", directory=f"{directory}", output_file=out_file, ranks_per_node=f"{ranks_per_node}", write_output=args['write_output'])
                #mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].setup_command(config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{files_per_rank}", test_repetition=f"{test_repetition}", directory=f"{directory}", offset=f"{offset}", output_file=out_file, write_data=f"{write_data}", read_data=f"{read_data}", ranks_per_node=f"{ranks_per_node}")
            
                with open(f"{command_log_dir}/mdtest_command_{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank", 'a') as file:
                    file.write(f"The following is the mdtest command")
                    tmp_cmd_string = ""
                    for cmd_el in mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].command:
                        tmp_cmd_string += f" {cmd_el}"
                    file.write(tmp_cmd_string)
                
                mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank"].run()
                
                start_time, end_time, elapsed_time = benchmark_tools.mdtest_start_end_elapsed_time(out_file)
                
                if args['timed']:
                    #elapsed_time, out_file, tmp_log_dir, tmp_log_filename, lower_threshold, higher_threshold, log_dir, args, among others
                    if elapsed_time <= lower_time_threshold or elapsed_time >= upper_time_threshold:
                        while elapsed_time <= lower_time_threshold or elapsed_time >= upper_time_threshold:
                            if 'unit_restart' in args:
                                if args['unit_restart'] == 1:
                                    pattern = '/'
                                    split_dir = re.split(pattern, directory)
                                    FS_root = '/'+split_dir[1]+'/'+split_dir[2]
                                    miscellaneous.restart_ceph_unit(FS_root)

                            source = out_file
                            tmp_log_filename = re.split('/', out_file)[len(re.split('/', out_file)) - 1]
                            destination = f"{tmp_log_dir}/{tmp_log_filename}"
                            shutil.move(source, destination)
                            
                            if elapsed_time <= lower_time_threshold:
                                multiple = lower_time_threshold / elapsed_time
                                new_files_per_rank = int(files_per_rank * multiple) + int(0.05 * files_per_rank)
                            if elapsed_time >= upper_time_threshold:
                                multiple = upper_time_threshold / elapsed_time
                                new_files_per_rank = int(files_per_rank * multiple) - int(0.05 * files_per_rank)
                            
                            if new_files_per_rank < 10:
                                new_files_per_rank = 10
                            #elif new_files_per_rank > 10000:
                            #    new_file_per_rank = 10000

                            out_file = f"{log_dir}/mdtest_output_{tmp_node}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank_timed"
                            
                            mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"] = handler_class.mdtestTool()
                            mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"].setup_command(config=config, config_file=f"{PyBench_root_dir}/{args['config']}", mpi_ranks=f"{tmp_rank}", files_per_rank=f"{new_files_per_rank}", directory=f"{directory}", output_file=out_file, ranks_per_node=f"{ranks_per_node}", write_output=args['write_output'])
                            with open(f"{command_log_dir}/mdtest_command_{tmp_node}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank_timed", 'a') as file:
                                file.write(f"The following is the mdtest command")
                                tmp_cmd_string = ""
                                for cmd_el in mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"].command:
                                    tmp_cmd_string += f" {cmd_el}"
                                file.write(tmp_cmd_string)
                            
                            mdtest_obj_dict[f"{tmp_node}_nodes_{ranks_per_node}_ranks_{new_files_per_rank}_new_files_per_rank"].run()
                            old_elapsed_time = elapsed_time
                            start_time, end_time, elapsed_time = benchmark_tools.mdtest_start_end_elapsed_time(out_file)

                            print (f"entered the optimizer. Old elapsed time: {old_elapsed_time}, New elapsed time: {elapsed_time}, old files_per_rank {files_per_rank}, new files per rank {new_files_per_rank}, multiple is: {multiple}")
                            files_per_rank = new_files_per_rank
                            if files_per_rank < 10:
                                files_per_rank = 10
                            #elif files_per_rank > 10000:
                            #    files_per_rank = 10000
                    total_files_optimized = files_per_rank * tmp_rank
                print(f"mdtest job {tmp_node}_nodes_{ranks_per_node}_ranks_{files_per_rank}_files_per_rank is finished. [s-{start_time}], [e-{end_time}], elapsed time: {elapsed_time}")
                
                sys.stdout.flush()
