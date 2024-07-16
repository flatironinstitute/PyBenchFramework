import os,sys
import re
import time
import mmap
import pathlib
import json
import socket
import subprocess
from cryptography.fernet import Fernet

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

def get_decrypted_password(opt_pass_file,opt_key_file):
    with open(opt_key_file, 'rb') as key_file:
        key = key_file.read()

    #load encrypted password
    with open(opt_pass_file, 'rb') as password_file:
        encrypted_password = password_file.read()

    #Decrypt
    f = Fernet(key)
    decrypted_password = f.decrypt(encrypted_password)

    return decrypted_password.decode()
'''
def restart_ceph_unit(path):

    def check_ceph_is_active(escaped_path, sudo_password):

        unit_filename = 'mnt-' + escaped_path + '.mount'
        unit_path = '/etc/systemd/system/' + unit_filename
        if not os.path.exists(unit_path):
            print("ERROR: Systemd unit '{}' does not exist".format(unit_path))
            sys.exit(1)

        try:
            command = ['sudo', '-S', 'systemctl', 'is-active', unit_filename]

            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output, error = process.communicate(sudo_password + '\n')

            print(f"{hostname} Output: ", output)
            print(f"{hostname} Errors: ", error)

            # Check the output
            if result.stdout.strip() == 'active':
                return 1
            else:
                return 0
        except subprocess.CalledProcessError as e:
            print(f"Failed to get active status for {unit_filename}: {e.stderr}")
            sys.exit(1)

    hostname = socket.gethostname()
    
    m = re.match('/mnt/cephtest[-_\w]*$', path)
    if not m:
        print("ERROR: Remount path must be /mnt/cephtest...")
        sys.exit(1)

    if not os.path.exists(path):
        print("ERROR: Path '{}' does not exist".format(path))
        sys.exit(1)

    escaped_path = path[5:]
    try:
        while True:
            ix = escaped_path.index('-')
            escaped_path = escaped_path[:ix] + '\\x2d' + escaped_path[ix+1:]
    except ValueError:
        pass

    try:
        key_file = os.getenv("KEY_FILE")
        if not key_file:
            raise ValueError(f"Environment variable 'KEY_FILE' is empty.")
            sys.exit(1)
    except KeyError:
        print("Error: Environment variable 'KEY_FILE' does not exist")
        sys.exit(1)
    except ValueError as ve:
        print(f"Error: {ve}")
        sys.exit(1)

    try:
        password_file = os.getenv("PASS_FILE")
        if not key_file:
            raise ValueError(f"Environment variable 'PASS_FILE' is empty.")
            sys.exit(1)
    except KeyError:
        print("Error: Environment variable 'PASS_FILE' does not exist")
        sys.exit(1)
    except ValueError as ve:
        print(f"Error: {ve}")
        sys.exit(1)

    print(key_file, password_file)

    command = ['sudo', '-S', 'python', '/mnt/cephadm/bin/iotest_helper.py', 'remount', path]

    sudo_password = miscellaneous.get_decrypted_password(password_file, key_file)

    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate(sudo_password + '\n')

    print(f"{hostname} Output: ", output)
    print(f"{hostname} Errors: ", error)
    
    active_status = 0
    active_counter = 0
    
    while active_status == 0:
        active_status = check_ceph_is_active(escaped_path, sudo_password)
        time.sleep(1)
        active_counter += 1

        if active_counter == 10:
            print(f"{hostname} systemd unit for {path} is not becoming active")
            sys.exit(1)
'''
