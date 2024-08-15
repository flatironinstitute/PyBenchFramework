from plot_util.serverless_plot import plot_serverless_FIO, return_FIO_data, plot_and_compare, mod_return_FIO_data
import sys
import re
import argparse


def handle_arguments():
    parser = argparse.ArgumentParser(description="This script automates plotting of benchmark results.")

    #universal
    parser.add_argument('--file', type=str, help="Path to the file containing space delimited job directories. Each line should contain a set of two directories to be plotted and compared, separated by a comma.")
    parser.add_argument('--paths', type=str, help="This option is used if the intention is to add a set of two directories as in-line arguments to be plotted and compared. The directories should be separated by a comma.")
    parser.add_argument('--full_paths', type=bool, help="Are you providing full (relative or absolute) directory paths or not? (0, 1, True, False)")

    args = parser.parse_args()
    args_dict = vars(args)

    return args_dict

def create_data_list(full_or_not, first_list, second_list):

    first_result_list = []
    second_result_list = []

    if len(first_list) != len(second_list):
        print ("List lengths must match")
        sys.exit()
    else:
        print(f"List lengths match. List 1 length {len(first_list)}, list 2 length {len(second_list)}")
        #print(f"{first_list}, {second_list}")
    
    if full_or_not:
        first_result_list, second_result_list = full_paths(first_list, second_list)
        #nodes_list1, bw_list1, iops_list1, processor_counts1 = first_result_list[0]
        #nodes_list2, bw_list2, iops_list2, processor_counts2 = second_result_list[0]
    elif not full_or_not:
        partial_paths()

    return first_result_list, second_result_list
    #print(first_result_list[0])
    #print(second_result_list[0])

def partial_paths(first_list, second_list):
    print("Partial paths code to be written...")

def full_paths(first_list, second_list):

    first_result_list = []
    second_result_list = []

    for i in range(len(first_list)):
        print(f"{first_list[i]}, {second_list[i]}")
        print("")
        try:
            first_result_list.append(list(mod_return_FIO_data(first_list[i], "testing_func", "4M")))
        except TypeError:
            print(f"Issue with returning FIO data from path provided '{first_list[i]}'") 
            sys.exit()
        try:
            second_result_list.append(list(mod_return_FIO_data(second_list[i], "testing_func", "4M")))
        except TypeError:
            print(f"Issue with returning FIO data from path provided '{second_list[i]}'") 
            sys.exit()

    return first_result_list, second_result_list

def extract_paths_from_file(filepath):
    first_job_list = []
    second_job_list = []

    try:
        with open (filepath, 'r') as file:
            for line in file:
                remove_quotes = line.replace('"','')
                tmp_line = remove_quotes.replace(' ','')
                tmp_line = tmp_line.replace("\n",'')
                first_job_list.append(re.split(',', tmp_line)[0])
                second_job_list.append(re.split(',', tmp_line)[1])
    except FileNotFoundError:
        print(f"File not found {filepath}")
        sys.exit()
    except IndexError:
        print(f"One of the lines in the file does not follow the format <first path> <second path>. Please ensure each line contains two paths, seperated by a comma.")
        sys.exit()

    return first_job_list, second_job_list

if __name__ == "__main__":
    
    args = handle_arguments()

    first_job_list = []
    second_job_list = []
    
    if 'file' in args and args['file'] is not None:
        first_job_list,second_job_list = extract_paths_from_file(args['file'])

    elif 'paths' in args.keys():
        first_job_list.append(re.split(',', args['paths'])[0])
        print(first_job_list)
        second_job_list.append(re.split(',', args['paths'])[1])
        print(second_job_list)

    full_or_not = args['full_paths']
    first_result_list, second_result_list = create_data_list(full_or_not, first_job_list, second_job_list)
    plot_and_compare(first_result_list, second_result_list)
