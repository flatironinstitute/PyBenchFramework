#!/bin/bash -e
#SBATCH -o logs/pi-%j.log
#SBATCH -e logs/pi-%j.err
#SBATCH -p scc
#SBATCH --ntasks-per-node=20
#SBATCH --nodes=10
#SBATCH --reservation=ceph_test
#SBATCH --time=40:00:00

root_dir="/mnt/home/skrit/Documents/PyBenchFramework"

filename="${root_dir}/host_files/${SLURM_JOB_ID}_hosts.file"

if [[ -f $filename ]]; then rm $filename; fi


pdsh -w $SLURM_JOB_NODELIST "source ${root_dir}/env_start ; IP=\$(ip a | grep 147 | awk '{print \$2}' | cut -d / -f 1 | head -n1); echo \"\${IP},5201\" >> ${filename}; fio --server=\"\${IP},5201\"" &

sleep 20 

if [[ -f ${filename} ]]; then
	#starting run to lay out all files
	#python python_runs/preallocate_all_files.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --split-hosts-file 1 --node-count 10,8,6,4,2,1 --hosts-file "${filename}" --config python_runs/EC63_config.yml 
	
	#starting run to lay out all files
	#python python_runs/preallocate_all_files.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --hosts-file "${filename}" --config python_runs/triple_rep_config.yml 

	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randread --block-size 4K --hosts-file "${filename}" --config python_runs/triple_rep_config.yml
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randread --block-size 4K --hosts-file "${filename}" --config python_runs/EC63_config.yml

	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randread --block-size 64K --hosts-file "${filename}" --config python_runs/triple_rep_config.yml
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randread --block-size 64K --hosts-file "${filename}" --config python_runs/EC63_config.yml

	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randread --block-size 4M --hosts-file "${filename}" --config python_runs/triple_rep_config.yml
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randread --block-size 4M --hosts-file "${filename}" --config python_runs/EC63_config.yml
	
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randwrite --block-size 4K --hosts-file "${filename}" --config python_runs/triple_rep_config.yml
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randwrite --block-size 4K --hosts-file "${filename}" --config python_runs/EC63_config.yml

	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randwrite --block-size 64K --hosts-file "${filename}" --config python_runs/triple_rep_config.yml
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randwrite --block-size 64K --hosts-file "${filename}" --config python_runs/EC63_config.yml

	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randwrite --block-size 4M --hosts-file "${filename}" --config python_runs/triple_rep_config.yml
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type randwrite --block-size 4M --hosts-file "${filename}" --config python_runs/EC63_config.yml

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type "read" --block-size 4M --hosts-file "${filename}" --config python_runs/EC63_config.yml

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type "read" --block-size 4M --hosts-file "${filename}" --config python_runs/triple_rep_config.yml

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type "write" --block-size 4M --hosts-file "${filename}" --config python_runs/EC63_config.yml

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --io-type "write" --block-size 4M --hosts-file "${filename}" --config python_runs/triple_rep_config.yml

else
	echo "File ${filename} creation failed... Exiting."
fi

pdsh -w $SLURM_JOB_NODELIST "ps aux | grep \"fio --server\" | grep -v bash | grep -v grep | awk '{ print \$2 }' | xargs kill"

