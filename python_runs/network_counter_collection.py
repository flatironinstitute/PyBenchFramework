import psutil
import socket
import time
import args_handler
import sys
from miscellaneous import ensure_log_directory_exists

stop_thread = False

def calculate_net_rate(interface_name, hostname, interval=1):
    old_stats = psutil.net_io_counters(pernic=True)
    time.sleep(interval)
    new_stats = psutil.net_io_counters(pernic=True)

    if interface_name in old_stats:
        print (f"monitoring only interface {interface_name} for traffic.")
        old_interface_stats = old_stats[interface_name]
        new_interface_stats = new_stats[interface_name]
        
        bytes_sent_per_sec = (new_interface_stats.bytes_sent - old_interface_stats.bytes_sent) / interval
        bytes_recv_per_sec = (new_inteface_stats.bytes_recv - old_inteface_stats.bytes_recv) / interval
        
    elif interface_name == '' or interface_name not in old_stats:
        print(f"monitoring all intefaces since --interface-name is either not specified or not found {hostname}")
        old_stats = psutil.net_io_counters()
        time.sleep(interval)
        new_stats = psutil.net_io_counters()
        bytes_sent_per_sec = (new_stats.bytes_sent - old_stats.bytes_sent) / interval
        bytes_recv_per_sec = (new_stats.bytes_recv - old_stats.bytes_recv) / interval


    return bytes_sent_per_sec, bytes_recv_per_sec

def convert_to_gbps(bytes_per_sec):
    GBPS_CONVERSION=1_073_741_824
    return bytes_per_sec / GBPS_CONVERSION


def monitor_traffic(args):

    global stop_thread

    root_dir = "/mnt/home/skrit/Documents/PyBenchFramework"

    hostname = socket.gethostname()
    rate_dict = {}

    slurm_job_number = args["slurm_job_number"] 

    if hostname == args["first_node"]:
        ensure_log_directory_exists(f"{root_dir}/network_stats/{slurm_job_number}", 1)

    with open(f"{root_dir}/network_stats/{slurm_job_number}/{hostname}_{args['job_number']}_{args['io_type']}", 'a') as file:
        while not stop_thread:

            epoch_time = int(time.time())

            bytes_sent, bytes_recv = calculate_net_rate(args['interface_name'], hostname)
            gb_sent = convert_to_gbps(bytes_sent)
            gb_recv = convert_to_gbps(bytes_recv)

            file.write(f"{epoch_time},{bytes_sent},{bytes_recv}\n")

            sys.stdout.flush()
