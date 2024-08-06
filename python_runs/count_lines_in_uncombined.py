import os
import sys
import time

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

def wait_until_line_count_is_node_count(file_path, hostname, node_count, check_interval=5):
    wait_time = 0
    while True:
        line_count = count_lines_in_file_direct(file_path)
        print(f"[{hostname}] Current line count is {line_count}. Waiting...")

        if line_count >= node_count:
            break

        time.sleep(check_interval)
        wait_time += 1 
        if wait_time >= 500:
            print(f"[{hostname}] Waited too long for uncombined to have the correct number of lines. Jobs and nodes are out of sync by over 40 minutes")
            sys.exit(1)

    print(f"[{hostname}] uncombined file has reached {node_count} lines. Moving onto next job...")

