import argparse
import yaml
import sys

#slurm job number
# triple replicated vs EC63 - FIO directory option
# block size? Multiple or single, either way need to decide which to test
# number of jobs? Not as an argument. At least not yet
# job length maybe
# Sequential vs random

def handle_arguments():
    parser = argparse.ArgumentParser(description="This script wraps FIO and facilitates long-running variable testing on an FS.")

    #universal
    parser.add_argument('--config', type=str, help="Path to the YAML config file.")
    parser.add_argument('--slurm-job-number', type=int, help="Slurm job number this script is running under")
    parser.add_argument('--directory', type=str, help="Directory to run the test in. This is where the test files will be created.")
    parser.add_argument('--first-node', type=str, help="The first node in the node list. Will execute some preperatory steps on this node")
    parser.add_argument('--benchmark', type=str, help="The benchmark you want to run.")
    parser.add_argument('--interface-name', type=str, help="The interface you want to monitor for inbound and outbound counters")
    parser.add_argument('--total-node-count', type=str, help="The total count of nodes in the job")
    parser.add_argument('--unit-restart', type=bool, help="Restart systemd unit (assumably ceph)")
    parser.add_argument('--node-count', type=str, help="Sequence of nodes that the benchmark should run with. e.g '1,2,4,6,8,10'")
    parser.add_argument('--job-note', type=str, help="insert a note for the job")
    parser.add_argument('--wait-for-others', type=bool, help="True if nodes should wait for each other to finish iterations, false if not (1 or 0)")
    parser.add_argument('--in-parts', type=bool, help="True if the sequences of benchmark arguments should be run iteratively. This usually means there will be multiple log files which will need to be taken into account in the parsing & plotting steps.")
    
    #ior portion
    parser.add_argument('--testFile', type=str, help="File/directory to run the IOR test suite on")
    parser.add_argument('--transfer-size',type=str, help="transfer size")
    parser.add_argument('--segment-count', type=str, help="segment count")
    parser.add_argument('--reorder-tasks', type=str, help="reorder tasks")
    parser.add_argument('--fsync', type=str, help="fsync")
    parser.add_argument('--output-file', type=str, help="output file")
    parser.add_argument('--output-format', type=str, help="output format")
    parser.add_argument('--deadline-for-stonewalling', type=int, help="Run IOR in timed mode instead of an indefinite time. All ranks stop at the same time.")
    parser.add_argument('--use-existing-file', type=bool, help="Use existing test file")

    #mdtest portion
    parser.add_argument('--mpi-ranks', type=str, help="Number of MPI ranks per node to use")
    parser.add_argument('--files-per-rank', type=str, help="Number of files to create per rank (mdtest)")
    parser.add_argument('--test-repetition', type=str, help="Number of times to repeat each test (mdtest)")
    parser.add_argument('--offset', type=str, help="Should there be a node offset? (if yes, 1, else ommit flag) (mdtest)")
    parser.add_argument('--write-data', type=str, help="Should mdtest write data into the files? Either 0 for no or a number of bytes (mdtest)")
    parser.add_argument('--read-data', type=str, help="Should mdtest read data from the files? Either 0 for no or a number of bytes (mdtest)")
    parser.add_argument('--timed', type=str, help="Specify the lower bound and upper bound of the time that the test should run for. Avoid values too close together. Units are seconds.")
    
    #fio portion
    parser.add_argument('--file-size', type=str, help="Specify the size of the file FIO should write out (per process)")
    parser.add_argument('--block-size', type=str, help="Block size that FIO should read/write at.")
    parser.add_argument('--job-number', type=str, help="Number or sequence of number of jobs per node that FIO should run. e.g '1,5,10,15'. This is per node count in --node-count")
    parser.add_argument('--time', type=int, help="Number of seconds that FIO should run for.")
    parser.add_argument('--io-type', type=str, help="write, read, randwrite, randread, among others. Which IO type should FIO issue?")
    parser.add_argument('--platform-type', type=str, help="Which platform are we using? This will decide output file path as well.")
    parser.add_argument('--split-hosts-file', type=bool, help="Should the wrapper split the original hosts file into subsections for the different iterations?")
    parser.add_argument('--hosts-file', type=str, help="Path to the intial hosts file which contains all hosts (At least FIO servers) involved.")
    parser.add_argument('--no-scrub', type=bool, help="(Ceph only) set noscrub and nodeepscrub flags on the ceph system. Requires passwordless SSH to the Ceph servers")
    parser.add_argument('--template-path', type=str, help="The path to the FIO template")

    args = parser.parse_args()
    args_dict = vars(args)

    config_dict = {}

    if args.config:
        with open(args.config, 'r') as file:
            config_dict = yaml.safe_load(file)

    # Merge config and inline arguments, giving precedence to inline arguments
    merged_dict = {**config_dict, **{k: v for k, v in args_dict.items() if v is not None}}

    # Set defaults if not provided
    merged_dict.setdefault('time', 300)
    merged_dict.setdefault('no_scrub', 0)
    merged_dict.setdefault('split_hosts_file', False)
    merged_dict.setdefault('interface_name', '')
    merged_dict.setdefault('write_data', '0')
    merged_dict.setdefault('read_data', '0')
    merged_dict.setdefault('wait_for_others', 1)

    # Check for required arguments
    #Trying a run without a hosts file to see if independent runs work
    #required_args = ['block_size', 'directory', 'io_type', 'platform_type', 'job_number', 'node_count', 'hosts_file', 'template_path']
    #required_args = ['block_size', 'directory', 'io_type', 'platform_type', 'job_number', 'node_count', 'template_path', 'benchmark']
    required_args = [ 'io_type', 'platform_type', 'benchmark']
    missing_args = [arg for arg in required_args if arg not in merged_dict or merged_dict[arg] is None]

    #print (f"{merged_dict['write_data']} {merged_dict['write_data']}") 
    if missing_args and not merged_dict["not_taken_into_account"]["in_parts"]:
        print(f"Error: Missing required arguments: {', '.join(missing_args)}")
        sys.exit(1)
    
    #print(merged_dict)
    return merged_dict
