import subprocess
import json
from abc import ABC, abstractmethod
import time
import os
from execute_ssh import execute_ssh_command
import re
import shlex
from datetime import datetime
import time
import sys
import psutil
import threading

class BenchmarkTool(ABC):
    def __init__(self):
        self.command = []
        self.output_format = "json"
        self.params = {}
        self.ceph_util = []
        
    @abstractmethod
    def setup_command(self, **params):
        """Setup the benchmark command with specific parameters."""
        self.params = params  # Ensure params are stored whenever setup_command is called
        pass

    @abstractmethod
    def parse_output(self, output):
        """Parse the benchmark-specific output."""
        pass

    def set_noscrub(self):
       
        noScrub = 0
        noDeepScrub = 0
        
        initial_output = execute_ssh_command('cephmon900', 'ceph', 'ceph status | grep flags' )
        print( initial_output)
        if initial_output:
            result = re.split(r'[,\s]+', initial_output)
        
            for res in result:
                if res == "noscrub":
                    noScrub = 1
                if res == "nodeep-scrub":
                    noDeepScrub = 1
        
            if noScrub == 0 or noDeepScrub == 0:
                print (f"one of the flags was unset (deep = {noDeepScrub}, scrub = {noScrub}), ensuring both are set...")
                
                #do setting work here
                print( execute_ssh_command('cephmon900', 'ceph', 'ceph osd set noscrub' ) )
                print( execute_ssh_command('cephmon900', 'ceph', 'ceph osd set nodeep-scrub' ) )
            else:
                print ("noscrub was already set, please ensure this is intended...")
        else:
            print("noscrub was not set, ensuring noscrub and nodeep-scrub are set...")
                
            #do setting work here
            print( execute_ssh_command('cephmon900', 'ceph', 'ceph osd set noscrub' ) )
            print( execute_ssh_command('cephmon900', 'ceph', 'ceph osd set nodeep-scrub' ) )

    def set_scrub(self):
        
        noScrub = 0
        noDeepScrub = 0
        
        initial_output = execute_ssh_command('cephmon900', 'ceph', 'ceph status | grep flags' )
        print(initial_output)
        if initial_output:
            result = re.split(r'[,\s]+', initial_output)
        
            for res in result:
                if res == "noscrub":
                    noScrub = 1
                if res == "nodeep-scrub":
                    noDeepScrub = 1
        
            if noScrub == 0 and noDeepScrub == 0:
                "noscrub was unset before this module completed, please ensure that is intended..."
            else:
                print("either noscrub or no-deepscrub is set, moving to unset")
                execute_ssh_command('cephmon900', 'ceph', 'ceph osd unset noscrub' )
                execute_ssh_command('cephmon900', 'ceph', 'ceph osd unset nodeep-scrub' )
        else:
            print ("noscrub was unset before this module completed, please ensure that is intended...")

    def run(self):
        
        try:
            start_time = time.time()
            result = subprocess.run(self.command, capture_output=True, text=True, check=True)
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Print standard output if the command succeeds
            print(datetime.now().time(), f"Time to complete: {elapsed_time}, Standard Output:")
            print(result.stdout)
            sys.stdout.flush()
        except subprocess.CalledProcessError as e:
            print("Error occurred:")
            print(f"Return code: {e.returncode}")
            print("Standard Error output:")
            print(e.stderr)
            sys.stdout.flush()

        if self.output_format == "json" and 'output' in self.params:
            output_file = self.params['output_file']
            max_retries = 3
            attempts = 0
            while attempts < max_retries:
                if os.path.exists(output_file):
                    with open(output_file, 'r') as file:
                        return json.load(file)
                time.sleep(20)  # Wait for 10 seconds before retrying
                print("...Waiting for output file...")
                attempts += 1
            print("Output file not found after several attempts.")
            sys.stdout.flush()
        else:
            output_file = self.params['output_file']
            with open(output_file, 'a') as file:
                file.write(result.stdout)

        #turn scrubbing back on
        #self.set_scrub()
        
        #return result.stdout

class newIORTool(BenchmarkTool):
    #pass
    #mpirun -n 64 ./ior -t 1m -b 16m -s 16 -F -C -e -o /path/to/TestFile
    def setup_command(self, **params):
        super().setup_command(**params)

        self.command = ["mpirun"]

        config_file = params.get('config_file')
        
        if config_file:
            pass
        else:
            raise ValueError("Configuration file must be specified. IOR...")
        
        mpi_ranks = params.get('mpi_ranks')
        filename = params.get('filename')
        ranks_per_node = params.get('ranks_per_node')
        block_size = params.get('block_size')
        transfer_size = params.get('transfer_size')
        segment_count = params.get('segment_count')
        reorder_tasks = params.get('reorder_tasks')
        fsync = params.get('fsync')
        output_file = params.get('output_file')
        output_format = params.get('output_format')
        deadline_for_stonewalling = params.get('deadline_for_stonewalling')
        io_type = params.get('io_type')
        use_existing_file = params.get('use_existing_file')

        # Required parameter: output file
        if mpi_ranks:
            self.command.extend(["-n", str(mpi_ranks)])
        else:
            raise ValueError("Number of MPI ranks must be specified (--mpi-ranks)")

        self.command.append("--map-by")
        self.command.append("node")
        
        if ranks_per_node:
            self.command.extend(["-N", str(ranks_per_node)])
        
        self.command.append("--verbose")
        self.command.append("ior")
        
        if block_size:
            self.command.extend(["-b", str(block_size)])
        
        if transfer_size:
            self.command.extend(["-t", str(transfer_size)])

        if segment_count:
            self.command.extend(["-s", str(segment_count)])
        
        if reorder_tasks:
            self.command.extend(["-C"])

        if fsync:
            self.command.extend(["-e"])

        if deadline_for_stonewalling != 0:
            self.command.extend(['-D', f"{deadline_for_stonewalling}"])
        else:
            pass

        if io_type == 'write':
            self.command.extend(['-w'])
        elif io_type == 'read':
            self.command.extend(['-r'])

        self.command.extend(['-k'])
        #self.command.extend(['-i', '1000'])
        #self.command.extend(['-T', '1'])
        self.command.extend(['-F'])

        if use_existing_file is True:
            self.command.extend(['-E'])

        # Required parameter: output file
        output_file = params.get('output_file')

        if filename:
            self.command.extend(["-o", str(filename)])
        else:
            raise ValueError("filename must be specified.")
        
        if output_file:
            self.command.extend(['-O', f"summaryFile={output_file}"])
        else:
            raise ValueError("Output file must be specified")

        if output_format:
            self.command.extend(['-O', f"summaryFormat={output_format}"])
        else:
            raise ValueError("Output file format must be specified")

    def parse_output(self, output):
        return "IOR no parsing yet."

class mdtestTool(BenchmarkTool):
    def setup_command(self, **params):
        super().setup_command(**params)

        self.command = ["mpirun"]
        
        config_file = params.get('config_file')
        if config_file:
            pass
        else:
            raise ValueError("Configuration file must be specified. mdtest...")

        mpi_ranks = params.get('mpi_ranks')
        files_per_rank = params.get('files_per_rank')
        test_repetition = params.get('test_repetition')
        directory = params.get('directory')
        offset = params.get('offset')
        #node_count = params.get('node_count')
        write_into_file = params.get('write_data')
        read_from_file = params.get('read_data')
        ranks_per_node = params.get('ranks_per_node')

        # Required parameter: output file
        if mpi_ranks:
            self.command.extend(["-n", str(mpi_ranks)])
        else:
            raise ValueError("Number of MPI ranks must be specified (--mpi-ranks)")

        self.command.append("--map-by")
        self.command.append("node")
        
        if ranks_per_node:
            self.command.extend(["-N", str(ranks_per_node)])
        
        self.command.append("--verbose")
        self.command.append("mdtest")
        
        if files_per_rank:
            self.command.extend(["-n", str(files_per_rank)])
        else:
            raise ValueError("Number of files per rank must be specified (--files-per-rank)")

        if test_repetition:
            self.command.extend(["-i", str(test_repetition)])
        
        if directory:
            self.command.extend(["-d", directory])
        else:
            raise ValueError("Directory must be specified. (--directory)")

        if offset:
            self.command.extend(["-N", str(offset)])

        # Required parameter: output file
        output_file = params.get('output_file')
        if output_file:
            pass
            #self.command.extend([">>", str(output_file)])
        else:
            raise ValueError("Output file must be specified")

        self.command.extend(["-Y"])
        
        if write_into_file: 
            self.command.extend(["-w", f"{write_into_file}"])
        if read_from_file:
            self.command.extend(["-e", f"{read_from_file}"])
    
    def parse_output(self, output):
        return "mdtest no parsing yet."


class FIOTool(BenchmarkTool):
    
    def setup_command(self, **params):
        super().setup_command(**params)  # Call the base method to store params
        
        self.command = [
                "fio",
                ]
        
        # Required parameter: configuration file
        config_file = params.get('config_file')        
        if config_file:
            self.command.append(f"{config_file}")
        else:
            raise ValueError("Configuration file must be specified")
        
        # Required parameter: output format
        output_format = params.get('output_format')
        if output_format:
            self.command.append(f"--output-format={output_format}")
        else:
            raise ValueError("Output format must be specified")
        
        # Required parameter: output file
        output_file = params.get('output_file')
        if output_file:
            self.command.append(f"--output={output_file}")
        else:
            raise ValueError("Output file must be specified")
    
        # Optional parameter: FIO host file
        host_file = params.get('host_file')
        host_list = params.get('host_list')

        if host_file:
            self.command.append(f"--client={host_file}")
        elif host_list:
            self.command.append(f"--client={host_list}")

    def parse_output(self, output):
        return {job['jobname']: {'Read BW': job['read']['bw'], 'Write BW': job['write']['bw']} for job in output['jobs']}

class IORTool(BenchmarkTool):
    def __init__(self, slurm_script_path):
        self.command = []
        self.slurm_script_path = slurm_script_path

    def setup_command(self, **params):
        super().setup_command(**params)  # Optionally handle common benchmark parameters

        # Initialize the command with mpirun
        num_procs = params.get('num_procs', 1)
        self.command = ["mpirun"]
        
        self.command.append("--map-by")
        self.command.append("node")

        self.command.extend(['-np', str(num_procs)])
        
        # Append the IOR executable
        self.command.append("ior")

        # Dynamically append other IOR specific parameters
        recognized_params = {'transfer_size': '-t', 'block_size': '-b', 
                             'segment_count': '-s', 'file_per_proc': '-F',
                             'collective': '-c', 'fsync': '-e'}
        
        for param, flag in recognized_params.items():
            value = params.get(param)
            if value is not None:
                if isinstance(value, bool) and value:
                    self.command.append(flag)
                elif isinstance(value, bool) and not value:
                    continue
                else:
                    self.command.extend([flag, str(value)])

        # Mandatory test file parameter
        if 'test_file' in params:
            self.command.extend(["-o", params['test_file']])
        else:
            raise ValueError("Test file must be specified")

    def run(self):
        # Generate the full IOR command
        command_str = ' '.join(shlex.quote(arg) for arg in self.command)
        
        # Read the Slurm script
        with open(self.slurm_script_path, 'r') as file:
            script_content = file.read()

        # Replace the placeholder with the IOR command
        modified_script_content = script_content.replace("<<IOR_RUN_LINE>>", command_str)

        # Write the modified script to a temporary file
        temp_script_path = "temp_slurm_script.sh"
        with open(temp_script_path, 'w') as file:
            file.write(modified_script_content)

        # Submit the Slurm job script
        submit_command = ["sbatch", temp_script_path]
        try:
            result = subprocess.run(submit_command, text=True, capture_output=True, check=True)
            print("Slurm Job Submitted:", result.stdout)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print("Error submitting Slurm job:", e.stderr)
            return e.stderr

    def parse_output(self, output):
        """Parse the benchmark-specific output."""
        pass

