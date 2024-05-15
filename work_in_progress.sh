#!/bin/bash -e
#SBATCH -o PyBenchFramework-%j.log
#SBATCH -e PyBenchFramework-%j.err
#SBATCH -p scc
#SBATCH --ntasks-per-node=20
#SBATCH --nodes=14
#SBATCH --reservation=ceph_test
#SBATCH --mem=1G

root_dir="/path/to/root/dir/"

filename="${root_dir}/host_files/${SLURM_JOB_ID}_hosts.file"

if [[ -f $filename ]]; then rm $filename; fi


pdsh -w $SLURM_JOB_NODELIST "module load modules/2.3-beta1 modules/2.3-beta2 modules/2.3-beta3 fio/3.36; IP=\$(ip a | grep 147 | awk '{print \$2}' | cut -d / -f 1 | head -n1); echo \"\${IP},5201\" >> ${filename}; fio --server=\"\${IP},5201\"" &

sleep 15

if [[ -f ${filename} ]]; then
	#python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 64K --directory /mnt/cephtest/test-rep3/skrit/fio/tmp/ --io-type randread --platform-type triple_replicated

	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 1M --directory /mnt/cephtest/test-rep3/skrit/fio/tmp/ --io-type randread --platform-type triple_replicated
else
	echo "File ${filename} creation failed... Exiting."
fi

pdsh -w $SLURM_JOB_NODELIST "ps aux | grep \"fio --server\" | grep -v bash | grep -v grep | awk '{ print \$2 }' | xargs kill"

