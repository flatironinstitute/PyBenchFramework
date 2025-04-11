import subprocess
import yaml
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
        self.elapsed_time = 0
        self.start_times = []
        self.end_times = []
        
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
            env = os.environ.copy()
            # Open the output file for appending
            if 'write_output' in self.params and self.params['write_output'] == 1:
                
                with open(self.params['output_file'], 'a') as output_file:
                    # Start the subprocess with stdout as PIPE to capture output
                    start_time = time.time()

                    #print (f"This is self.command: {self.command} .. handler_class:101")
                    # Run the command and capture output in real-time
                    process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

                    # Read and print the output in real-time
                    for line in process.stdout:
                        # Print to terminal
                        print(line, end='')

                        # Write to the output file
                        output_file.write(line)

                    # Wait for the process to complete
                    process.wait()

                    end_time = time.time()
                    elapsed_time = end_time - start_time

                    self.elapsed_time = elapsed_time
                    print(datetime.now().time(), f"Time to complete: {elapsed_time}")
                
            else:
                # Start the subprocess and wait for it to finish
                start_time = time.time()
                result = subprocess.run(self.command, capture_output=False, text=True, check=True, env=env)
                end_time = time.time()
                elapsed_time = end_time - start_time

        except subprocess.CalledProcessError as e:
            print("Error occurred:")
            print(f"Return code: {e.returncode}")
            print("Standard Error output:")
            print(e.stderr)
            sys.stdout.flush()
            sys.stderr.flush()


class test_ior_tool(BenchmarkTool):

    def setup_command(self, **params):
        super().setup_command(**params)

        self.command = ["mpirun"]
        
        config_params = params.get('config')

        mpi_ranks = params.get('mpi_ranks') 
        filename = config_params['filename']
        ranks_per_node = params.get('ranks_per_node')
        output_file = params.get('output_file')
        output_format = config_params
        
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

        not_iteratable = ['mpi_ranks', 'node_count', 'filename', 'config_options', 'command_extensions', 'job_note', 'platform_type', 'unit_restart', 'io_type', 'output_file']

        if filename:
            self.command.extend(["-o", str(filename)])
        else:
            raise ValueError("filename must be specified.")

        #print(config_params)
        for param, value in config_params.items():
            if param not in not_iteratable:
                self.command.extend([f"-{param}={str(value)}"])
            if param == 'config_options':
                for key, val in value.items():
                    self.command.extend([f"-{key}={str(val)}"])
            if param == 'command_extensions':
                for i in value:
                    self.command.extend([f"-{i}"])

        if output_file:
            self.command.extend(['-O', f"summaryFile={output_file}"])
        else:
            raise ValueError("Output file must be specified")

    def parse_output(self, output):
        return "IOR no parsing yet."

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
        '''
        list_of_opts = [ "api", "refNum", "blockSize", "collective", "reorderTasksConstant", "interTestDelay", "deadlineForStonewalling", "fsync", "useExistingTestFile", "scriptFile", "filePerProc", "intraTestBarriers", "setTimeStampSignature", "showHelp", "showHints", "repetitions", "individualDataSets", "outlierThreshold", "setAlignment", "keepFile", "keepFileWithError", "data", "multiFile", "memoryPerNode", "noFill", "numTasks", "testFile", "string", "preallocate", "useSharedFilePointer", "quitOnError", "taskPerNodeOffset", "readFile", "checkRead", "segmentCount", "useStridedDatatype", "transferSize", "maxTimeDuration", "uniqueDir", "hintsFileName", "verbose", "useFileView", "writeFile", "checkWrite", "singleXferAttempt", "reorderTasksRandomSeed", "fsyncPerWrite", "randomOffset", "reorderTasksRandom" ]

        with open (config_file, 'r') as opts_file:
            config = yaml.safe_load(opts_file)
            print(config)
        '''
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

'''
class test_mdtest_tool(BenchmarkTool):
    pass
    def setup_command(self, **params):
        super().setup_command(**params)

        self.command = ["mpirun"]

        config_params = params.get('config')

        mpi_ranks = params.get('mpi_ranks')
        ranks_per_node = params.get('ranks_per_node')
        files_per_rank = params.get('files_per_rank')
        directory = params.get('directory')

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

        not_iteratable = ['mpi_ranks', 'node_count', 'filename', 'config_options', 'command_extensions', 'job_note', 'platform_type', 'unit_restart', 'io_type', 'output_file', 'timed']

        #test_repetition = params.get('test_repetition')
        #offset = params.get('offset')
        #write_into_file = params.get('write_data')
        #read_from_file = params.get('read_data')
#    pass
'''

class mdtestTool(BenchmarkTool):
    def setup_command(self, **params):
        super().setup_command(**params)
        
        config_file = params.get('config_file')
        if config_file:
            pass
        else:
            raise ValueError("Configuration file must be specified. mdtest...")

        mpi_ranks = params.get('mpi_ranks')
        files_per_rank = params.get('files_per_rank')
        directory = params.get('directory')
        ranks_per_node = params.get('ranks_per_node')
        # Required parameter: output file
        output_file = params.get('output_file')
        config_params = params.get('config')

        self.command = ["mpirun"]

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

        if directory:
            self.command.extend(["-d", directory])
        else:
            raise ValueError("Directory must be specified. (--directory)")

        
        not_iteratable = ['mpi_ranks', 'directory', 'files_per_rank', 'node_count', 'timed', 'config_options', 'command_extensions', 'job_note', 'platform_type', 'unit_restart', 'io_type', 'output_file', 'write_output', 'in_parts']

        for param, value in config_params.items():
            if param not in not_iteratable:
                self.command.extend([f"-{param}={str(value)}"])
            if param == 'config_options':
                for key, val in value.items():
                    self.command.extend([f"-{key}={str(val)}"])
            if param == 'command_extensions':
                for i in value:
                    self.command.extend([f"-{i}"])

        if output_file:
            pass
            #self.command.extend([">>", str(output_file)])
        else:
            raise ValueError("Output file must be specified")

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

