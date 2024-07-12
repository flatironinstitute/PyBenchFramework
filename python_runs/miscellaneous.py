import os,sys
import re
import time
import mmap
import pathlib
import json
import socket

def ensure_log_directory_exists(directory, createdir):
    if not os.path.exists(directory):
        if createdir == 1:
            os.makedirs(directory)

def reset_file_contents(original_file_contents, args, job_count, single_block_size):

    # Reset file_contents to the original template for each iteration
    file_contents = original_file_contents
    file_contents = file_contents.replace("__block_size__", single_block_size)
    file_contents = file_contents.replace("__number_of_jobs__", f"{job_count}")
    file_contents = file_contents.replace("__dir_var__", args['directory'])
    file_contents = file_contents.replace("__io_type_var__", args['io_type'])
    file_contents = file_contents.replace("__time_var__",f"{args['time']}")
    file_contents = file_contents.replace("__hostname__",f"{socket.gethostname()}")

    return file_contents

def load_json_results(filename):
    data = {}
    if filename.endswith(".json"):
        with open(filename, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {filename}")

    jobname = data['jobs'][0]['jobname']
    if jobname == "randread":
        jobname = "read"
    elif jobname == "randwrite":
        jobname = "write"
    bw = data['jobs'][0][jobname]['bw']
    iops = data['jobs'][0][jobname]['iops']

    return bw, iops

def count_lines(filename):
    with open(filename, 'r') as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as m:
            return sum(1 for line in iter(m.readline, b""))

def insert_entry_and_check_completion (filename, hostname, total_node_count):

    with open(filename, 'a') as file:
        file.write(f"{hostname} \n")
    
    start_waiting = time.time()

    line_count_is_sufficient = 0
    while line_count_is_sufficient == 0:
        line_count = count_lines(filename)
        stop_waiting = time.time()
        if line_count == total_node_count:
            line_count_is_sufficient = 1
        how_long = stop_waiting - start_waiting

        if how_long > 10:
            type_line_count = type(line_count)
            type_node_count = type(total_node_count)
            print (f"waited too long. File line count is {line_count} and total node count is {total_node_count}... type line count is {type_line_count} type total node count {type_node_count}")
            break

def grep_string(filename, search_string):
    line_numbers = []
    with open(filename, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            if re.search(search_string, line):
                line_numbers.append(line_number)
    return line_numbers[0]
