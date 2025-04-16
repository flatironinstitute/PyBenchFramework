import os, sys

def log_and_analyze_data_points(log_dir, fio_object): 

    #Let's try rate-limiting to see how that effects start and end times.
    print(log_dir)
    print(fio_object)
