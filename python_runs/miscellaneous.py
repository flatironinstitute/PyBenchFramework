import os,sys
import re
import time
import mmap
import pathlib
import fcntl
import yaml
import json
import socket
import subprocess
from cryptography.fernet import Fernet

def ensure_log_directory_exists(directory, createdir):
    if not os.path.exists(directory):
        if createdir == 1:
            os.makedirs(directory)

def create_hostname_mapping(log_dir):
    hostname = f"{socket.gethostname()}"
    #insert hostname into file
    #find line that hostname was inserted into
    #combine line index and generic name like so: hostxx, where xx stands for line index
    log_path = f"{log_dir}/hostname_mapping.txt"

    '''
    with open (log_path, 'a') as file:
        # Lock file for writing
        fcntl.flock(file, fcntl.LOCK_EX)
        file.write(f"{hostname}\n")
        file.flush()
        # Unlock file
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()
    '''

    with open(log_path, 'r+') as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        hostname_found = False
        lines = file.readlines()

        for idx, line in enumerate(lines):
            host_index = idx + 1
            if hostname in line:
                mapped_hostname = f"{hostname}:host{host_index}\n"
                lines[idx] = mapped_hostname
                hostname_found = True

        if hostname_found:
            pass
        else:
            #print (f"hostname {hostname} not found in hostname_mapping.txt file!")
            #sys.exit()
            line_index = len(lines)
            host_index = line_index + 1
            mapped_hostname = f"{hostname}:host{host_index}\n"
            lines.append(mapped_hostname)

        file.seek(0)
        file.writelines(lines)
        file.truncate()

        file.flush()
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()
    
def get_hostname_mapping(hostname,log_dir):
    log_path = f"{log_dir}/hostname_mapping.txt"
    mapped_hostname = ''
    Err = 1
    hostname = socket.gethostname()

    while Err >= 1 and Err <= 3:
        with open (log_path, 'r') as file:
            fcntl.flock(file, fcntl.LOCK_EX)
            lines = file.readlines()
            
            for line in lines:
                if hostname in line:
                    try:
                        mapped_hostname = re.split(':', line.strip())[1]
                        Err = 0
                    except IndexError as e:
                        if Err == 3:
                            print("Hostname mapping failed 3 times... Exiting.")
                            fcntl.flock(file, fcntl.LOCK_UN)
                            file.close()
                            sys.exit()
                        Err += 1

                        fcntl.flock(file, fcntl.LOCK_UN)
                        file.close()
                        
        if Err >= 1:
            print("Retrying to create the hostname map for {hostname}")
            create_hostname_mapping(log_dir)

    return mapped_hostname

def reset_file_contents(original_file_contents, args, job_count, single_block_size, log_dir):

    #get mapping of hostname to generic index entry
    hostname = socket.gethostname()
    mapped_hostname = get_hostname_mapping(hostname,log_dir)

    # Reset file_contents to the original template for each iteration
    file_contents = original_file_contents
    file_contents = file_contents.replace("__block_size__", single_block_size)
    file_contents = file_contents.replace("__number_of_jobs__", f"{job_count}")
    file_contents = file_contents.replace("__dir_var__", args['directory'])
    file_contents = file_contents.replace("__io_type_var__", args['io_type'])
    file_contents = file_contents.replace("__time_var__",f"{args['time']}")
    file_contents = file_contents.replace("__hostname__",f"{mapped_hostname}")
    file_contents = file_contents.replace("__file_size__",f"{args['file_size']}")

    return file_contents

def load_ior_json_results(filename, log_dir):
    data = {}
    strings_to_remove = ["Writing output to ", "WARNING:"]
    
    name_without_path = re.split("/", filename)[len(re.split("/",filename)) - 1]

    with open(filename, 'r') as file:
        lines = file.readlines()

    with open(f"{log_dir}/tmp_files/{name_without_path}.unedited", 'w') as file:
        file.writelines(lines)
        file.flush()

    filtered_lines = [line for line in lines if not any(s in line for s in strings_to_remove)]

    with open(filename, 'w') as file:
        file.writelines(filtered_lines)
        file.flush()

    with open(filename, 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            print(f"IOR workflow: Error decoding JSON From file: {filename}")
    bw = {}
    iops = {}
    
    #account for multiple result types from IOR results files (read,write as opposed to just one or the other)
    try: 
        if len(data['tests'][0]['Results'][0]) == 1:
            label = data['tests'][0]['Results'][0][0]['access']

            bw[f"{label}"] = data['tests'][0]['Results'][0][0]['bwMiB']
            iops[f"{label}"] = data['tests'][0]['Results'][0][0]['iops']
        elif len(data['tests'][0]['Results'][0]) == 2:
            label1 = data['tests'][0]['Results'][0][0]['access']
            label2 = data['tests'][0]['Results'][0][1]['access']
            
            bw[f"{label1}"] = data['tests'][0]['Results'][0][0]['bwMiB'] 
            bw[f"{label2}"] = data['tests'][0]['Results'][0][1]['bwMiB'] 
            iops[f"{label1}"] = data['tests'][0]['Results'][0][0]['iops'] 
            iops[f"{label2}"] = data['tests'][0]['Results'][0][1]['iops'] 

    except KeyError as e:
        print(f'''Issue with results for either:
        bw = data['tests'][0]['Results'][0][0]['bwMiB']
        iops = data['tests'][0]['Results'][0][0]['iops']
        In JSON decode of file: {filename}''')
    except Exception as e:
        print(f"An unexpected error occurred: {e}. IOR, filename: {filename}")
    
    
    return bw, iops

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

def restart_ceph_unit(path):

    def check_ceph_is_active(escaped_path):
        #, sudo_password):

        unit_filename = 'mnt-' + escaped_path + '.mount'
        unit_path = '/etc/systemd/system/' + unit_filename
        if not os.path.exists(unit_path):
            print("ERROR: Systemd unit '{}' does not exist".format(unit_path))
            sys.exit(1)

        try:
            command = ['systemctl', 'is-active', unit_filename]

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            #output, error = process.communicate(sudo_password + '\n')
            
            print(f"{hostname} Ceph is active? Output: ", result.stdout)
            print(f"{hostname} Ceph is active? Errors: ", result.stderr)

            is_active = result.stdout.strip()
            
            # Check the output
            if is_active == 'active':
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
    
    '''
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
    '''
    
    #command = ['sudo', '-S', 'python', '/mnt/cephadm/bin/iotest_helper.py', 'remount', path]
    command = ['sudo', '/mnt/cephadm/bin/iotest_helper.py', 'remount', path]
    
    #sudo_password = get_decrypted_password(password_file, key_file)
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #output, error = process.communicate(sudo_password + '\n')
    
    print(f"{hostname} Ceph restart? Output: ", result.stdout)
    print(f"{hostname} Ceph restart? Errors: ", result.stderr)
    
    active_status = 0
    active_counter = 0
    
    while active_status == 0:
        active_status = check_ceph_is_active(escaped_path)
                #, sudo_password)
        time.sleep(1)
        active_counter += 1

        if active_counter == 10:
            print(f"{hostname} systemd unit for {path} is not becoming active")
            sys.exit(1)

def get_config_params(config_file):

    #enabling classes in handler_class.py to read a list object containing dicts parsed from the input YAML files
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
        raise ValueError("Configuration file must be specified.")

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

    return config
