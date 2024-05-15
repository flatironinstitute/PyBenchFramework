import subprocess
import json
from abc import ABC, abstractmethod
import time
import os
from execute_ssh import execute_ssh_command
import re
import shlex

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
        """set scrubbing off"""
        #self.set_noscrub()
        
        #Execute the constructed benchmark command.
        result = subprocess.run(self.command, capture_output=True, text=True, check=True)
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
        
        #turn scrubbing back on
        #self.set_scrub()
        
        #return result.stdout

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
        
        self.command.extend(['--map-by', 'ppr:10:node'])
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

# Example usage for FIO
#fio = FIOTool()
#fio.setup_command(path="/dev/sda", block_size="4k", io_depth="32", rw="randwrite")
#output_data = fio.run()
#print(fio.parse_output(output_data))

# Implement other tools like IOR and Ozone in a similar fashion

'''
# Example usage
params = {
    'num_procs': 64,
    'host_file': 'myhosts.txt',
    'transfer_size': '1m',
    'block_size': '16m',
    'segment_count': '16',
    'file_per_proc': True,
    'collective': True,
    'fsync': True,
    'test_file': 'filename',
    'summary_format': 'JSON'
}

ior_tool = IORTool()
ior_tool.setup_command(**params)
output = ior_tool.run()
print(output)
'''

"""
# Example usage
slurm_script_path = 'path_to_slurm_script.sh'
params = {
    'num_procs': 4,
    'host_file': 'hosts.txt',
    'transfer_size': '1m',
    'block_size': '256m',
    'segment_count': 16,
    'file_per_proc': True,
    'collective': True,
    'fsync': True,
    'test_file': 'testFile.ior'
}

ior_tool = IORTool(slurm_script_path)
ior_tool.setup_command(**params)
output = ior_tool.run()
"""