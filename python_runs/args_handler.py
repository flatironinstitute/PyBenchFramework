import argparse

#slurm job number
# triple replicated vs EC63 - FIO directory option
# block size? Multiple or single, either way need to decide which to test
# number of jobs? Not as an argument. At least not yet
# job length maybe
# Sequential vs random

def handle_arguments():
    parser = argparse.ArgumentParser(description="This script wraps FIO and facilitates long-running variable testing on an FS.")

    parser.add_argument('--slurm-job-number', type=int, required=False, help="Slurm job number this script is running under")
    parser.add_argument('--block-size', type=str, required=True, help="Block size that FIO should read/write at.")
    parser.add_argument('--directory', type=str, required=True, help="Directory to run the test in. This is where the test files will be created.")
    parser.add_argument('--job-number', type=str, required=False, help="Number of jobs per node that FIO should run.")
    parser.add_argument('--time', type=int, default=300, help="Number of seconds that FIO should run for.")
    parser.add_argument('--io-type', type=str, required=True, help="write, read, randwrite, randread, among others. Which IO type should FIO issue?")
    parser.add_argument('--platform-type', type=str, required=True, help="Which platform are we using? This will decide output file path as well.")
    parser.add_argument('--split-hosts-file', type=str, required=False, default=False, help="Should the wrapper split the original hosts file into subsections for the different iterations?")

    args = parser.parse_args()
    
    args_dict = vars(args)

    print(args_dict)

    return args_dict
