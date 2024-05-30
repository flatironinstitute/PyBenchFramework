#!/bin/bash -e
#SBATCH -o logs/pi-%j.log
#SBATCH -e logs/pi-%j.err
#SBATCH -p scc
#SBATCH --ntasks-per-node=20
#SBATCH --nodes=10
#SBATCH --reservation=ceph_test
#SBATCH --time=40:00:00

root_dir="/mnt/home/skrit/Documents/benchmark_handler/"

filename="${root_dir}/host_files/${SLURM_JOB_ID}_hosts.file"

if [[ -f $filename ]]; then rm $filename; fi


pdsh -w $SLURM_JOB_NODELIST "source /mnt/home/skrit/Documents/benchmark_handler/env_start; IP=\$(ip a | grep 147 | awk '{print \$2}' | cut -d / -f 1 | head -n1); echo \"\${IP},5201\" >> ${filename}; fio --server=\"\${IP},5201\"" &

sleep 15

if [[ -f ${filename} ]]; then
	#starting run to lay out all files
	python python_runs/preallocate_all_files.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "write" --platform-type EC63 --split-hosts-file "1,2,4,6,8,10" 
	
	#starting run to lay out all files
	python python_runs/preallocate_all_files.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "write" --platform-type triple_replicated 

	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4K --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "randread" --platform-type triple_replicated 
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4K --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "randread" --platform-type EC63

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 64K --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "randread" --platform-type triple_replicated 

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 64K --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "randread" --platform-type EC63 

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "randread" --platform-type triple_replicated
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "randread" --platform-type EC63
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4K --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "randwrite" --platform-type triple_replicated
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4K --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "randwrite" --platform-type EC63

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 64K --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "randwrite" --platform-type triple_replicated

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 64K --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "randwrite" --platform-type EC63 

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "randwrite" --platform-type triple_replicated
	
	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "randwrite" --platform-type EC63

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "read" --platform-type triple_replicated 

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "read" --platform-type EC63 

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-rep3/skrit/fio/tmp/ --io-type "write" --platform-type triple_replicated

	#if [[ -f $filename ]]; then rm $filename; fi
	python python_runs/multi_node.py --slurm-job-number ${SLURM_JOB_ID} --block-size 4M --directory /mnt/cephtestk/test-ec63/skrit/fio-test/tmp/ --io-type "write" --platform-type EC63

else
	echo "File ${filename} creation failed... Exiting."
fi

pdsh -w $SLURM_JOB_NODELIST "ps aux | grep \"fio --server\" | grep -v bash | grep -v grep | awk '{ print \$2 }' | xargs kill"

