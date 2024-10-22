#!/bin/bash -e
#SBATCH -o logs/mdtest-%j.log
#SBATCH -e logs/mdtest-%j.err
#SBATCH -p scc
#SBATCH -p scc
#SBATCH --nodes=24
#SBATCH --exclusive
#SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi5,type=fuse],cephfs[cluster=cephtest-fi5,type=kernel]"
##SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi5,type=fuse,version=16.2.15.1]"
#SBATCH -C genoa

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')

#python python_runs/prep_work.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/cephtest_fuse/interactive_test.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/cephtest_kernel/interactive_test.yml --first-node ${first_node}

sleep 10

#python python_runs/run.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/cephtest_fuse/interactive_test.yml --first-node ${first_node}

python python_runs/run.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/cephtest_kernel/interactive_test.yml --first-node ${first_node}
