import os
import time
import sys
from datetime import datetime

def write_barrier_line(file_path, iteration, hostname, phase):
    """
    Append a line such as:
    iteration=1,hostname=node1,phase=1
    to the barrier file, then flush.
    """
    line = f"iteration={iteration},hostname={hostname},phase={phase}\n"
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(line)
        f.flush()  # ensure it is actually written
        os.fsync(f.fileno())  # ensure it’s on disk

def count_barrier_lines(file_path, iteration, phase):
    """
    Return how many unique hostnames have lines matching
    iteration=<iteration> and phase=<phase>.
    """
    if not os.path.exists(file_path):
        return 0

    unique_hosts = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Example line: iteration=1,hostname=node1,phase=2
            # A simple parse approach:
            parts = line.split(',')
            # We expect 3 parts: ["iteration=1", "hostname=node1", "phase=2"]
            if len(parts) != 3:
                continue

            iter_part = parts[0].split('=')[-1].strip()
            host_part = parts[1].split('=')[-1].strip()
            phase_part = parts[2].split('=')[-1].strip()

            # Compare vs our iteration & phase
            if iter_part == str(iteration) and phase_part == str(phase):
                unique_hosts.add(host_part)

    return len(unique_hosts)

def barrier_phase(file_path, iteration, hostname, phase, node_count, timeout=600, check_interval=1):
    """
    Phase barrier:
      - Write (iteration, hostname, phase) to file_path
      - Wait for all nodes to do the same 
    """
    # 1) Write our line
    write_barrier_line(file_path, iteration, hostname, phase)

    # 2) Wait for all nodes
    waited = 0
    while True:
        count = count_barrier_lines(file_path, iteration, phase)
        if count == node_count:
            print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Phase={phase}, iteration={iteration} has {count}/{node_count} lines. Barrier passed.")
            return
        else:
            print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Phase={phase}, iteration={iteration} sees only {count}/{node_count} lines. Waiting...")
            time.sleep(check_interval)
            waited += check_interval
            if waited >= timeout:
                print(f"{datetime.now().strftime('%b %d %H:%M:%S')} [{hostname}] Timed out waiting for barrier, Phase={phase}, iteration={iteration}. Exiting.")
                sys.exit(1)

