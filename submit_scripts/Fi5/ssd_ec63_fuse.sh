#!/bin/bash -e
#SBATCH -o logs/ceph-fi5-fuse-ssd-ec63-%j.log
#SBATCH -e logs/ceph-fi5-fuse-ssd-ec63-%j.err
#SBATCH -p scc
#SBATCH --nodes=24
#SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi5,type=fuse]"
#SBATCH --exclusive
#SBATCH -C genoa
#SBATCH --dependency=afterany:4104260

# Define root directory
root_dir=$PyBench_root_dir

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')
#cephtest-fi5/test_fuse_ec63_ssd.yml
python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "write" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "read" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randread" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randwrite" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --first-node ${first_node}

sleep 10

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --first-node ${first_node} --total-node-count 24 --node-count 24 --template-path /mnt/home/skrit/Documents/testing_clones/clone1/PyBenchFramework/examples/template/starting_template.fio --job-number 16 

rm -f results/write/Fi5-ec63-ssd-fuse/${SLURM_JOB_ID}/*.tmp
rm -f results/write/Fi5-ec63-ssd-fuse/${SLURM_JOB_ID}/*.json

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "read" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --block-size 4M --first-node ${first_node} --total-node-count 24

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "write" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --block-size 4M --first-node ${first_node} --total-node-count 24

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "randread" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --first-node ${first_node} --total-node-count 24

srun --nodes=24 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "randwrite" --config python_runs/config/cephtest-fi5/test_fuse_ec63_ssd.yml --first-node ${first_node} --total-node-count 24
