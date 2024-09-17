#!/bin/bash -e
#SBATCH -o logs/client_modules-ssd-kernel-rep3-%j.log
#SBATCH -e logs/client_modules-ssd-kernel-rep3-%j.err
#SBATCH -p scc
#SBATCH --nodes=20
#SBATCH --reservation=worker_test
#SBATCH --nodelist=worker[7372-7374,7377-7379,7382-7386,7388-7390,7392-7397]
#SBATCH --exclusive

# Define root directory
root_dir=$PyBench_root_dir

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "write" --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "read" --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randread" --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randwrite" --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node}

sleep 10

srun --nodes=20 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node} --total-node-count 20 --node-count 20 --template-path /mnt/home/skrit/Documents/testing_clones/clone1/PyBenchFramework/examples/template/starting_template.fio --job-number 48 

#replace 'nvme_rep3_kernel' with the platform type you specify in the YAML config files
rm -f results/write/nvme_rep3_kernel/${SLURM_JOB_ID}/*.tmp
rm -f results/write/nvme_rep3_kernel/${SLURM_JOB_ID}/*.json

srun --nodes=20 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "read" --block-size 4M --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node} --total-node-count 20

srun --nodes=20 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "write" --block-size 4M --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node} --total-node-count 20

srun --nodes=20 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "randread" --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node} --total-node-count 20

srun --nodes=20 python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --io-type "randwrite" --config python_runs/config/tmp_runs/nvme_test_kernel_ssd_rep3.yml5 --first-node ${first_node} --total-node-count 20