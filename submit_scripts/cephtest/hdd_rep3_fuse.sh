#!/bin/bash -e
#SBATCH -o logs/cephtest-fuse-hddrep3-%j.log
#SBATCH -e logs/cephtest-fuse-hddrep3-%j.err
#SBATCH -p scc
#SBATCH --nodes=24
#SBATCH --comment "FI_JOB_RESOURCES=cephfs[cluster=cephtest-fi9,type=fuse]"
#SBATCH --exclusive
#SBATCH -C genoa
##SBATCH --dependency=afterany:4540887

# Define root directory
root_dir=$PyBench_root_dir

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')
python python_runs/prep_work.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "write" --config python_runs/config/cephtest/test_fuse_rep3.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "read" --config python_runs/config/cephtest/test_fuse_rep3.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randread" --config python_runs/config/cephtest/test_fuse_rep3.yml --first-node ${first_node}

python python_runs/prep_work.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --io-type "randwrite" --config python_runs/config/cephtest/test_fuse_rep3.yml --first-node ${first_node}

sleep 10

mpirun -n 384 --bind-to none --map-by node -N 16 python python_runs/run.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --config python_runs/config/cephtest/test_fuse_rep3.yml --first-node ${first_node} --total-node-count 24 --node-count 24 --template-path /mnt/home/skrit/Documents/testing_clones/clone1/PyBenchFramework/examples/template/starting_template.fio --job-number 16 

rm -f results/write/cephtest-rep3-fuse/${SLURM_JOB_ID}/*.tmp
rm -f results/write/cephtest-rep3-fuse/${SLURM_JOB_ID}/*.json

mpirun -n 384 --bind-to none --map-by node -N 16 python python_runs/run.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --io-type "read" --config python_runs/config/cephtest/test_fuse_rep3.yml --block-size 4M --first-node ${first_node} --total-node-count 24

mpirun -n 384 --bind-to none --map-by node -N 16 python python_runs/run.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --io-type "write" --config python_runs/config/cephtest/test_fuse_rep3.yml --block-size 4M --first-node ${first_node} --total-node-count 24

mpirun -n 384 --bind-to none --map-by node -N 16 python python_runs/run.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --io-type "randread" --config python_runs/config/cephtest/test_fuse_rep3.yml --first-node ${first_node} --total-node-count 24

mpirun -n 384 --bind-to none --map-by node -N 16 python python_runs/run.py --benchmark "fio-independent-ranks" --slurm-job-number ${SLURM_JOB_ID} --io-type "randwrite" --config python_runs/config/cephtest/test_fuse_rep3.yml --first-node ${first_node} --total-node-count 24

