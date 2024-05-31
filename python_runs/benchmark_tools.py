import os,sys

def count_lines(filename):
    with open(filename, 'r') as file:
        line_count = 0
        for line in file:
            line_count += 1
    return line_count

def create_node_list(node_string, filename, root_dir, job_num):
    
    node_list = []
    node_count_list = []
    
    node_count_list = split_arg_sequence(str(node_string), '--split-host-file')

    with open(filename, 'r') as file:
        for node_name in file:
            stripped_name = node_name.strip()
            node_list.append(stripped_name)

    for count in node_count_list:
        i=0
        with open(f"{root_dir}/host_files/{job_num}_{count}_hosts.file", 'a') as file:
            while i < count:
                file.write(f"{node_list[i]}\n")
                i += 1

def split_arg_sequence(sequence, arg):
    sequence_list = []

    try:
        string_sequence_list = sequence.split(",")
        sequence_list = [int(num) for num in string_sequence_list]
    except ValueError as ve:
        print(f"ValueError: {ve}. Please ensure the input string for {arg} contains only numbers separated by commas.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occured: {e} \n {arg}")
        sys.exit(1)

    return sequence_list
