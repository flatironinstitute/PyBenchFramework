#!/bin/bash -e
#SBATCH -o logs/ceph-fi5-fuse-ssdec63-%j.log
#SBATCH -e logs/ceph-fi5-fuse-ssdec63-%j.err
#SBATCH -p scc
#SBATCH --nodes=24
#SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi5,type=fuse],cephfs[cluster=cephtest-fi5,type=kernel]"
#SBATCH --exclusive
#SBATCH -C genoa

# Define root directory
root_dir=$PyBench_root_dir

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "write" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "read" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randread" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randwrite" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --first-node ${first_node}

sleep 10

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --first-node ${first_node} --total-node-count 24 --node-count 24 --template-path /mnt/home/skrit/Documents/testing_clones/clone1/PyBenchFramework/examples/template/starting_template.fio --job-number 16 

rm -f results/write/nvme_ec63_fuse/${SLURM_JOB_ID}/*.tmp
rm -f results/write/nvme_ec63_fuse/${SLURM_JOB_ID}/*.json

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "read" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --block-size 4M --first-node ${first_node} --total-node-count 24

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "write" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --block-size 4M --first-node ${first_node} --total-node-count 24

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "randread" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --first-node ${first_node} --total-node-count 24

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "randwrite" --config python_runs/config/nvme_test_fuse_ssd_ec63.yml --first-node ${first_node} --total-node-count 24
