# PyBenchFramework
#throw this change out
This application is being used with slurm but it can run on its own.

User must set the environment variable "PyBench_root_dir" to run run.py. Try to use mdtest_env to start the environment for MDTEST or env_start for FIO. Don't use both at the same time.

The app needs a root directory to read templates and store intermediate config files as well as log files and the like.

Options can be included as arguments to 'run.py' or as fields in a YAML config file. The config file for an FIO job looks like so:

<pre>
slurm_job_number: 
block_size: "4M,64K,4K"
directory: /mnt/cephtest-fi5k/test-rep3-ssd/skrit/fio
time: 120
io_type: write
platform_type: nvme_rep3_kernel
split_hosts_file: 0
job_number: '48,16,8,4,2,1'
node_count: 20,16,8,4,2,1
hosts_file:
no_scrub: 0
unit_restart: 1
template_path: /mnt/home/skrit/Documents/testing_clones/clone1/PyBenchFramework/examples/template/template.fio
</pre>

The config file for an mdtest job looks like so:

<pre>
mpi_ranks: 40,30,20,10,5 
directory: /mnt/cephtestk/test-ec63/skrit/mdtest
files_per_rank: 20,10,5
test_repetition: 3
slurm_job_number:
io_type: metadata
platform_type: kernel_EC63 
offset: 1
write_data: '3901'
read_data: '3901'
node_count: 10,5,1
</pre>

One thing to note is that the main loop takes mpi ranks and multiplies it to the node count. For example, when mpi_ranks is 5 and node_count is 1, mpirun is given '-n 5' for a total of 5 mpi ranks. When mpi_ranks is 5 and node_count is 10, mpirun is given '-n 50' (5 * 10) which is distributed across 10 nodes (--map-by node -N 10).

'slurm_job_number' should, at least for now, be an inline argument. Keep in mind inline arguments are likely separated by - rather than _ --help should show all arguments as they should be inline.

Under the 'submit_scripts' folder, you'll see several slurm scripts. 'mdtest.sh' is a good template for submitting mdtest jobs and the scripts starting with 'ssd...' or 'hdd...' are good templates for FIO jobs.
