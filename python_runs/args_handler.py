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
    
    #mdtest portion
    parser.add_argument('--mpi-ranks', type=str, help="Number of MPI ranks to use (only mdtest, for now)")
    parser.add_argument('--files-per-rank', type=str, help="Number of files to create per rank (mdtest)")
    parser.add_argument('--test-repetition', type=str, help="Number of times to repeat each test (mdtest)")
    parser.add_argument('--offset', type=str, help="Should there be a node offset? (if yes, 1, else ommit flag) (mdtest)")
    
    #fio portion
    parser.add_argument('--block-size', type=str, help="Block size that FIO should read/write at.")
    parser.add_argument('--job-number', type=str, help="Number or sequence of number of jobs per node that FIO should run. e.g '1,5,10,15'. This is per node count in --node-count")
    parser.add_argument('--node-count', type=str, help="Sequence of nodes that FIO should run on. e.g '1,2,4,6,8,10'")
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

    # Check for required arguments
    #Trying a run without a hosts file to see if independent runs work
    #required_args = ['block_size', 'directory', 'io_type', 'platform_type', 'job_number', 'node_count', 'hosts_file', 'template_path']
    #required_args = ['block_size', 'directory', 'io_type', 'platform_type', 'job_number', 'node_count', 'template_path', 'benchmark']
    required_args = ['directory', 'io_type', 'platform_type', 'benchmark']
    missing_args = [arg for arg in required_args if arg not in merged_dict or merged_dict[arg] is None]

    if missing_args:
        print(f"Error: Missing required arguments: {', '.join(missing_args)}")
        sys.exit(1)
    
    #print(merged_dict)
    return merged_dict
