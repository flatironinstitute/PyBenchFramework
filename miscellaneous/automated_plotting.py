from plot_util.serverless_plot import plot_serverless_FIO, return_FIO_data, plot_and_compare, mod_return_FIO_data
import sys
import re
import argparse
import matplotlib.pyplot as plt


def handle_arguments():
    parser = argparse.ArgumentParser(description="This script automates plotting of benchmark results.")

    #universal
    parser.add_argument('--file', type=str, help="Path to the file containing space delimited job directories. Each line should contain a set of two directories to be plotted and compared, separated by a comma.")
    parser.add_argument('--paths', type=str, help="This option is used if the intention is to add a set of two directories as in-line arguments to be plotted and compared. The directories should be separated by a comma.")
    parser.add_argument('--full_paths', type=bool, help="Are you providing full (relative or absolute) directory paths or not? (0, 1, True, False)")
    parser.add_argument('--one_path', type=bool, help="Use when plotting a single job without a comparison. boolean")
    parser.add_argument('--benchmark', type=str, help="Specify which benchmark the results are coming from (FIO,IOR,MDTEST)")
    parser.add_argument('--output_path', type=str, help="Specify the output path.")
    parser.add_argument('--block_size', type=str, help="Specify the block size (FIO,IOR)")

    args = parser.parse_args()
    args_dict = vars(args)

    return args_dict

def create_data_list(full_or_not, all_list,benchmark,block_size):
#def create_data_list(full_or_not, first_list, second_list):

    first_result_list = []
    second_result_list = []

    all_result_list = []
    
    #print("here create_data_list")
    if len(all_list) == 1:
        if full_or_not:
            all_result_list.append(list(full_paths(all_list[0],benchmark,block_size)))
        elif not full_or_not:
            partial_paths()
        #print(all_result_list)
        return all_result_list
    '''
    if second_list == 0:
        if full_or_not:
            first_result_list = full_paths(first_list, 0)
        elif not full_or_not:
            partial_paths()
        return first_result_list
    '''
    
    first_length = -1
    first_iter = 0

    for path_list_element in all_list:
        if first_length == -1:
            first_length = len(path_list_element)
        else:
            if len(path_list_element) == first_length:
                pass
            else:
                print(f"List lengths don't match, {path_list_element}")
                sys.exit()

        if full_or_not:
            #for i in all_list:
            all_result_list.append(list(full_paths(path_list_element,benchmark,block_size)))
    
    #print(all_result_list)
    return all_result_list
    print("All list lengths match")
    
def partial_paths(first_list, second_list):
    print("Partial paths code to be written...")

#def full_paths(first_list, second_list):
def full_paths(all_job_list, benchmark, block_size):

    first_result_list = []
    second_result_list = []
    
    all_result_list = []

    #print(all_job_list)
    #print(len(all_job_list))
    if len(all_job_list) == 1:
        for i in range(len(all_job_list)):
            try:
                first_result_list.append(list(mod_return_FIO_data(all_job_list[i], "testing_func", block_size, benchmark)))
            except TypeError:
                print(f"Issue with returning FIO data from path provided '{all_job_list[0][i]}'") 
                sys.exit()

        return first_result_list

    for list_instance in all_job_list:
        try:
            #print("list_instance")
            all_result_list.append(list(mod_return_FIO_data(list_instance, "testing_func", block_size, benchmark)))
            #print(list(mod_return_FIO_data(list_instance, "testing_func", "4M")))
        except TypeError:
            print(f"Issue with returning FIO data from path provided '{list_instance[i]}'") 
            sys.exit()
        #print("LIST INSTANCE IS FINISHED")
    return all_result_list

#def extract_paths_from_file(filepaths, one_path):
def extract_paths_from_file(filepath, one_path):
    
    first_job_list = []
    second_job_list = []
    
    all_job_list = []

    
    #for filepath in filepaths:
    try:
        with open (filepath, 'r') as file:
            for line in file:
                remove_quotes = line.replace('"','')
                tmp_line = remove_quotes.replace(' ','')
                tmp_line = tmp_line.replace("\n",'')

                if one_path:
                    #first_job_list.append(tmp_line)
                    all_job_list.append(tmp_line)
                else:
                    #first_job_list.append(re.split(',', tmp_line)[0])
                    #second_job_list.append(re.split(',', tmp_line)[1])
                    all_job_list.append(re.split(',', tmp_line))
                    #print(re.split(',', tmp_line))
                    #print("FILE LIST ELEMENT IS FINISHED")
                    #print("")
    except FileNotFoundError:
        print(f"File not found {filepath}")
        sys.exit()
    except IndexError:
        print(f"One of the lines in the file does not follow the format <first path> <second path>. Please ensure each line contains two paths, seperated by a comma.")
        sys.exit()

    if one_path:
        return first_job_list

    return all_job_list
    '''

    try:
        with open (filepath, 'r') as file:
            for line in file:
                remove_quotes = line.replace('"','')
                tmp_line = remove_quotes.replace(' ','')
                tmp_line = tmp_line.replace("\n",'')

                if one_path:
                    first_job_list.append(tmp_line)
                else:
                    first_job_list.append(re.split(',', tmp_line)[0])
                    second_job_list.append(re.split(',', tmp_line)[1])
    except FileNotFoundError:
        print(f"File not found {filepath}")
        sys.exit()
    except IndexError:
        print(f"One of the lines in the file does not follow the format <first path> <second path>. Please ensure each line contains two paths, seperated by a comma.")
        sys.exit()

    if one_path:
        return first_job_list

    return first_job_list, second_job_list
    '''

if __name__ == "__main__":
    
    args = handle_arguments()

    first_job_list = []
    second_job_list = []
    
    all_job_list = []
    all_result_list = []

    output_path = args['output_path']

    if 'benchmark' in args.keys():
        benchmark=args['benchmark'].strip()
    else:
        print("Benchmark not provided! Please provide the benchmark used to generate results!")
        sys.exit()

    if args['block_size']:
        block_size=args['block_size']
    else:
        if benchmark.upper() == "IOR" or benchmark.lower() == "ior" or benchmark.upper() == "FIO" or benchmark.lower() =="fio":
            print("Block size not provided! Please provide the block size when running this script for FIO or IOR!")
            sys.exit()

    if 'file' in args and args['file'] is not None and not args['one_path']:
        #first_job_list,second_job_list = extract_paths_from_file(args['file'], 0)
        all_job_list = extract_paths_from_file(args['file'], 0)
    elif 'file' in args and args['file'] is not None and args['one_path']:
        first_job_list = extract_paths_from_file(args['file'], args['one_path'])

    elif 'paths' in args.keys():
        first_job_list.append(re.split(',', args['paths'])[0])
        #print(first_job_list)
        second_job_list.append(re.split(',', args['paths'])[1])
        #print(second_job_list)

    full_or_not = args['full_paths']
    if not args['one_path']:
        #first_result_list, second_result_list = create_data_list(full_or_not, first_job_list, second_job_list)
        all_result_list = create_data_list(full_or_not, all_job_list, benchmark, block_size)
        #print(all_result_list)
        for i in all_result_list:
            #print("Here?")
            #print(i)
            #print(len(i))
            #print("LIST ELEMENT FINISHED")
            #print("\n")
            ##print(i)
            plot_and_compare(i, output_path)
        #plot_and_compare(first_result_list, second_result_list)
    else:
        first_result_list = create_data_list(full_or_not, first_job_list,benchmark, block_size)
        for i in range(len(first_job_list)):
            fig, ax1, ax2 = plot_serverless_FIO(first_job_list[i], "testing auto plot", "4M")
            plt.savefig(f"{output_path}/result{i}.svg", format="svg")
