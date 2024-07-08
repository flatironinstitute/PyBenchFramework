import os,sys
import pathlib
import json

def ensure_log_directory_exists(directory, createdir):
    if not os.path.exists(directory):
        if createdir == 1:
            os.makedirs(directory)

def reset_file_contents(original_file_contents, args, job_count):

    # Reset file_contents to the original template for each iteration
    file_contents = original_file_contents
    file_contents = file_contents.replace("__block_size__", args['block_size'])
    file_contents = file_contents.replace("__number_of_jobs__", f"{job_count}")
    file_contents = file_contents.replace("__dir_var__", args['directory'])
    file_contents = file_contents.replace("__io_type_var__", args['io_type'])
    file_contents = file_contents.replace("__time_var__",f"{args['time']}")

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
    bw = data['jobs'][0][jobname]['bw']
    iops = data['jobs'][0][jobname]['iops']

    return bw, iops
