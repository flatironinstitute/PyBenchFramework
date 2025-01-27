import os
import sys
import time
from datetime import datetime

def get_block_size(file_path):
    stats = os.statvfs(file_path)
    return stats.f_bsize

def count_lines_in_file_direct(file_path):
    try:
        # Get the filesystem block size
        block_size = get_block_size(file_path)
        
        # Open the file with O_DIRECT flag
        fd = os.open(file_path, os.O_RDONLY | os.O_DIRECT) 
        # Pre-allocate a bytearray with the block size
        buffer = bytearray(block_size)
        
        line_count = 0
        while True:
            # Read from the file into the buffer
            n = os.read(fd, block_size)
            if not n:
                break
            # Copy the read data into the bytearray
            buffer[:len(n)] = n
            
            # Convert buffer to string and count the lines
            data = buffer[:len(n)].decode('utf-8')
            line_count += data.count('\n')
        
        # Close the file descriptor
        os.close(fd)
        return line_count
    except FileNotFoundError:
        return 0

def wait_until_line_count_is_node_count(file_path, hostname, node_count, total_intervals, check_interval=5):
    wait_time = 0
    while True:
        line_count = count_lines_in_file_direct(file_path)
        print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Current line count is {line_count}. Filename ({file_path}) Waiting...")

        if line_count > node_count:
            print (f"Line count in intermediate results file is higher than the node count, possible duplicate reporting. This could be a result of using the same output directory more than once... File ({file_path})")
            sys.exit()
        if int(line_count) <= int(node_count):
            #print(f"Line count is {line_count} and type is {type(line_count)}, node count is {node_count} and type is {type(node_count)}")
            found = 0
            with open (file_path, 'r') as file:
                lines = file.readlines()

                for i in lines:
                    if hostname in i:
                        found += 1
                    else:
                        pass

            if found == 0:
                return 0
            if found > 1:
                print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] hostname found more than once in file!")
                sys.exit()
            if found == 1 and line_count == node_count:
                return 1

        time.sleep(check_interval)
        wait_time += 1 
        if wait_time >= total_intervals:
            print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Waited too long for uncombined to have the correct number of lines. Jobs and nodes are out of sync by over 40 minutes")
            sys.exit(1)

    print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] uncombined file has reached {node_count} lines. Moving onto next job...")

