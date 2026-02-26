#!/bin/bash -e
#SBATCH -o logs/mdtest-%j.log
#SBATCH -e logs/mdtest-%j.err
#SBATCH -p scc
#SBATCH --nodes=24
#SBATCH --exclusive
#SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi5,type=fuse,version=18.2.6.1],cephfs[cluster=cephtest-fi5,type=kernel]"
##SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi9,type=fuse],cephfs[cluster=cephtest-fi9,type=kernel]"
#SBATCH -C genoa

#source /mnt/home/skrit/Documents/testing_clones/clone1/PyBenchFramework/mdtest_env.template 

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')

python python_runs/prep_work.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config ${PyBench_mdtest_configs}/cephtest_fuse/new_structure_code_testing.yml --first-node ${first_node}

#python python_runs/prep_work.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config ${PyBench_mdtest_configs}/cephtest_kernel/new_structure_code_testing.yml --first-node ${first_node}

sleep 10

python python_runs/run.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config ${PyBench_mdtest_configs}/cephtest_fuse/new_structure_code_testing.yml --first-node ${first_node}

#python python_runs/run.py --benchmark "testmdtest" --slurm-job-number ${SLURM_JOB_ID} --config ${PyBench_mdtest_configs}/cephtest_kernel/new_structure_code_testing.yml --first-node ${first_node}
