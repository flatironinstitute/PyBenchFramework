#!/bin/bash -e
#SBATCH -o logs/mdtest-%j.log
#SBATCH -e logs/mdtest-%j.err
#SBATCH -p scc
#SBATCH --nodes=10
#SBATCH --reservation=ceph_test
##SBATCH -C ib-icelake
##SBATCH --time=40:00:00

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')

python python_runs/prep_work.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_kernel_EC63_config.yml --first-node ${first_node}

sleep 10

python python_runs/run.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_kernel_EC63_config.yml --first-node ${first_node}

#python python_runs/prep_work.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_kernel_triple_rep_config.yml --first-node ${first_node}

#sleep 10

#python python_runs/run.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_kernel_triple_rep_config.yml --first-node ${first_node}

#############################

#python python_runs/prep_work.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_fuse_triple_rep_config.yml --first-node ${first_node}

#sleep 10

#python python_runs/run.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_fuse_triple_rep_config.yml --first-node ${first_node}

#python python_runs/prep_work.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_fuse_EC63_config.yml --first-node ${first_node}

#sleep 10

#python python_runs/run.py --benchmark "mdtest" --slurm-job-number ${SLURM_JOB_ID} --config python_runs/mdtest_config/mdtest_fuse_EC63_config.yml --first-node ${first_node}
