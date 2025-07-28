# PyBenchFramework
This application is designed to be used with `slurm` but it can run on its own.

## Installation (development)
```sh
python3 -m venv /path/to/venv
source /path/to/venv/bin/activate
git clone https://github.com/flatironinstitute/PyBenchFramework --branch cleanup
cd PyBenchFramework
pip install -e .
rehash # might not be necessary, depending on shell
```

## Running
```sh
source /path/to/venv/bin/activate
mpirun -n 2 pybench-run --benchmark "fio-independent-ranks" --slurm-job-number 0 --io-type "read" --config examples/YAML_templates/FIO_templates/test_kernel_rep3_ssd.yml --block-size 4M --first-node $(hostname -s) --total-node-count 1
```
Options can be included as arguments to 'run.py' or as fields in a YAML config file. The config
file for an FIO job looks like so:

### Configuration
```yaml
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
```

The config file for an mdtest job looks like so:

```yaml
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
```

## Slurm submission
All `submit_scripts` are currently broken.
