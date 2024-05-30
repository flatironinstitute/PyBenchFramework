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
    
    try:
        string_num_list = node_string.split(",")
        node_count_list = [int(num) for num in string_num_list]
    except ValueError as ve:
        print("ValueError: {ve}. Please ensure the input string for --split-hosts-file contains only numbers separated by commas.")
        return None
    except Exception as e:
        print(f"An unexpected error occured: {e}")
        return None

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

