#!/bin/bash -e
#SBATCH -o logs/ior_test-%j.log
#SBATCH -e logs/ior_test-%j.err
#SBATCH -p scc
#SBATCH --nodes=20
#SBATCH --exclusive
#SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi5,type=fuse,lock],cephfs[cluster=cephtest-fi5,type=kernel,lock]"
#SBATCH -C genoa

# Define root directory
root_dir=$PyBench_root_dir

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')


python python_runs/prep_work.py --benchmark "testIORTool" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/IOR_config/example_write.yml --first-node ${first_node}
python python_runs/prep_work.py --benchmark "testIORTool" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/IOR_config/example_read.yml --first-node ${first_node}


sleep 10
#sleep 500

python python_runs/run.py --config python_runs/IOR_config/example_write.yml --benchmark "testIORTool" --slurm-job-number ${SLURM_JOB_ID} --first-node ${first_node} --total-node-count 20
python python_runs/run.py --config python_runs/IOR_config/example_read.yml --benchmark "testIORTool" --slurm-job-number ${SLURM_JOB_ID} --first-node ${first_node} --total-node-count 20
