#!/bin/bash -e
#SBATCH -o logs/client_modules-%j.log
#SBATCH -e logs/client_modules-%j.err
#SBATCH -p scc
#SBATCH --nodes=10
#SBATCH --reservation=ceph_test
##SBATCH -C ib-icelake
##SBATCH --time=40:00:00

# Define root directory
root_dir="/mnt/home/skrit/Documents/PyBenchFramework"

block_size="1M"

first_node=$(echo $SLURM_JOB_NODELIST | cut -d '-' -f 1 | awk -F '[' '{ print $1$2 }')

start_time=$(date +%s)

echo "${first_node}"

python python_runs/prep_work.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 1M --config python_runs/fsync_test_ceph_test.yml --first-node ${first_node}

sleep 10

srun --nodes=$SLURM_JOB_NUM_NODES python python_runs/run.py --benchmark "fio-serverless" --slurm-job-number ${SLURM_JOB_ID} --block-size 1M --config python_runs/fsync_test_ceph_test.yml --first-node ${first_node}

end_time=$(date +%s)

# Run the Python multi-node script
echo "Start FIO jobs"
echo "Stop FIO jobs"

# Print the start and end times
echo "Start time: ${start_time}"
echo "End time: ${end_time}"

#wait $srun_pid

echo "srun command has finished."
