from plot_util.serverless_plot import plot_serverless_FIO, return_FIO_data, plot_and_compare, mod_return_FIO_data, convert_mdtest_data, read_mdtest_json_data,plot_and_compare_mdtest, convert_mdtest_data_in_parts
from plot_util.text_based_comparison import *
import sys
import re
import argparse
import matplotlib.pyplot as plt
import pandas as pd


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
    parser.add_argument('--comparison', type=str, help="Specify the type of comparison you want to perform (temporrary)...")

    args = parser.parse_args()
    args_dict = vars(args)

    return args_dict

def create_data_list(full_or_not, all_list,benchmark,block_size):

    first_result_list = []
    second_result_list = []

    all_result_list = []
    
    all_job_list = []
    for i in all_list:
        
        tmp_sub_job_list = []
        for j in i:
            if not j:
                pass
            else:
                tmp_sub_job_list.append(j)
        
        all_job_list.append(tmp_sub_job_list)
    
    if len(all_job_list) == 1:
        if full_or_not:
            all_result_list.append(list(full_paths(all_job_list[0],benchmark,block_size)))
        elif not full_or_not:
            partial_paths()
        #print(all_result_list)
        return all_result_list
    
    first_length = -1
    first_iter = 0
    for path_list_element in all_job_list:
        '''
        first_length = -1
        for path in path_list_element:
            print(len(path))
            if first_length == -1:
                first_length = len(path)
            else:
                if len(path) == first_length:
                    pass
                else:
                    print(f"List lengths don't match, {path_list_element}")
                    sys.exit()
        '''
        if full_or_not:
            #for i in all_job_list:
            all_result_list.append(list(full_paths(path_list_element,benchmark,block_size)))
    
    #print(all_result_list)
    return all_result_list
    print("All list lengths match")
    
def partial_paths(first_list, second_list):
    print("Partial paths code to be written...")

def full_paths(all_job_list, benchmark, block_size):

    first_result_list = []
    second_result_list = []
    
    all_result_list = []

    #print(f"Length of all job list = {len(all_job_list)}")

    if len(all_job_list) == 1:
        if benchmark.upper == "IOR" or benchmark.lower() == "ior" or benchmark.upper == "FIO" or benchmark.lower() == "fio":
            for i in range(len(all_job_list)):
                try:
                    first_result_list.append(list(mod_return_FIO_data(all_job_list[i], "testing_func", block_size, benchmark)))
                except TypeError:
                    print(f"Issue with returning FIO data from path provided '{all_job_list[0][i]}'") 
                    sys.exit()
        if benchmark.upper() == "MDTEST" or benchmark.lower() == "mdtest":
            convert_mdtest_data(all_job_list[0])
            first_result_list.append(read_mdtest_json_data(all_job_list[0]))
        elif benchmark.upper() == "MDTESTINPARTS" or benchmark.lower() == "mdtestinparts":
            convert_mdtest_data_in_parts(all_job_list[0])
            first_result_list.append(read_mdtest_json_data(all_job_list[0]))
        return first_result_list

    for list_instance in all_job_list:
        if benchmark.upper == "IOR" or benchmark.lower() == "ior" or benchmark.upper == "FIO" or benchmark.lower() == "fio":
            try:
                all_result_list.append(list(mod_return_FIO_data(list_instance, "testing_func", block_size, benchmark)))
            except TypeError:
                print(f"Issue with returning FIO data from path provided '{list_instance}'") 
                sys.exit()
        if benchmark.upper() == "MDTEST" or benchmark.lower() == "mdtest":
            #print(f"These are the jobs read from the input file: {all_job_list}")
            #print( "MDTEST workflow multiple --------" )
            convert_mdtest_data(list_instance)
            all_result_list.append(read_mdtest_json_data(list_instance))
            #sys.exit()
        if benchmark.upper() == "MDTESTINPARTS" or benchmark.lower() == "mdtestinparts":
            convert_mdtest_data_in_parts(list_instance)
            all_result_list.append(read_mdtest_json_data(list_instance))
    return all_result_list

def extract_paths_from_file(filepath, one_path):
    
    first_job_list = []
    second_job_list = []
    
    all_job_list = []

    try:
        with open (filepath, 'r') as file:
            for line in file:
                if line.strip():
                    remove_quotes = line.replace('"','')
                    tmp_line = remove_quotes.replace(' ','')
                    tmp_line = tmp_line.replace("\n",'')

                    if one_path:
                        all_job_list.append(tmp_line)
                    else:
                        all_job_list.append(re.split(',', tmp_line))
    except FileNotFoundError:
        print(f"File not found {filepath}")
        sys.exit()
    except IndexError:
        print(f"One of the lines in the file does not follow the format <first path> <second path>. Please ensure each line contains two paths, seperated by a comma.")
        sys.exit()

    if one_path:
        return first_job_list

    return all_job_list

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
        else:
            block_size = None


    if 'file' in args and args['file'] is not None and not args['one_path']:
        all_job_list = extract_paths_from_file(args['file'], 0)
    elif 'file' in args and args['file'] is not None and args['one_path']:
        first_job_list = extract_paths_from_file(args['file'], args['one_path'])

    elif 'paths' in args.keys():
        first_job_list.append(re.split(',', args['paths'])[0])
        second_job_list.append(re.split(',', args['paths'])[1])

    full_or_not = args['full_paths']
    print(args['comparison'])
    if 'comparison' in args.keys() and args['comparison'] is not None:
        if args['comparison'].lower() == "text" or args['comparison'].upper() == "TEXT":
            print('here')
            all_result_list = create_data_list(full_or_not, all_job_list, benchmark, block_size)
            for i in all_result_list:
                new_text_comparison(i, benchmark)

            sys.exit()
    if not args['one_path']:
        all_result_list = create_data_list(full_or_not, all_job_list, benchmark, block_size)
        for i in all_result_list:
            if benchmark.upper() == "MDTEST" or benchmark.lower() == "mdtest" or benchmark.upper() == "MDTESTINPARTS" or benchmark.lower() == "mdtestinparts":
                plot_and_compare_mdtest(i, output_path)
            else:
                #all_result_list is a list of lists. Each of these lists corresponds to a line in the input file, which stores a comma-delimited list of job result directories. In this secondary 'job list', each 'job list' element corresponds to one of the jobs in the line from the input file and is a list that contains a list of lists, which are node_count_list, bw_list, iops_list, processor_counts, plot_title, node_list which are each a list of lists storing individual values (node counts, node dicts, processor counts)
                plot_and_compare(i, output_path, all_result_list)
    else:
        first_result_list = create_data_list(full_or_not, first_job_list,benchmark, block_size)
        if benchmark.upper() == "MDTEST" or benchmark.lower() == "mdtest":
            #print("IN MDTEST WORKFLOW")
            plot_and_compare_mdtest(i, output_path)
        else:
            for i in range(len(first_job_list)):
                fig, ax1, ax2 = plot_serverless_FIO(first_job_list[i], "testing auto plot", "4M")
                plt.savefig(f"{output_path}/result{i}.svg", format="svg")
