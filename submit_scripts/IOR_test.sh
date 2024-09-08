#!/bin/bash -e
#SBATCH -o logs/ior_test-%j.log
#SBATCH -e logs/ior_test-%j.err
#SBATCH -p scc
#SBATCH --nodes=20
##SBATCH --nodelist=worker[7382-7384,7386-7392]
#SBATCH --exclusive
#SBATCH --reservation worker_test
#SBATCH --exclude=submit_scripts/nodes_to_exclude

# Define root directory
root_dir=$PyBench_root_dir

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')

python python_runs/prep_work.py --benchmark "newIORTool" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/IOR_config/write.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "newIORTool" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/IOR_config/read.yml --first-node ${first_node}

sleep 10

python python_runs/run.py --benchmark "newIORTool" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/IOR_config/write.yml --first-node ${first_node} --total-node-count 20

python python_runs/run.py --benchmark "newIORTool" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/IOR_config/read.yml --first-node ${first_node} --total-node-count 20
