# PyBenchFramework

This application is being used with slurm but it can run on its own.

User must set the environment variable "PyBench_root_dir" to run multi_run.py.
The app needs a root directory to read templates and store intermediate config files as well as log files and the like.

Options can be included as arguments to 'multi_run.py' or as fields in a YAML config file. The config file looks like so:

<pre>
slurm_job_number: 
block_size: 4k
directory: /mnt/cephtest/test-ec63/skrit/fio-test/tmp  
time: 180 
io_type: write
platform_type: EC63 
split_hosts_file: 0
job_number: 15,10,5,1
node_count: 10,8,6,4,2,1 
hosts_file:
no_scrub: 1
template_path: /mnt/home/skrit/Documents/PyBenchFramework/examples/template/template.fio
</pre>

'slurm_job_number' should, at least for now, be an inline argument. The same holds true for 'hosts_file'. Keep in mind inline arguments are likely separated by - rather than _ --help should show all arguments as they should be inline.
