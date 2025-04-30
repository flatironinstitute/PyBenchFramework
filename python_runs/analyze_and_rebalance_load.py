import os, sys, re

def log_and_analyze_data_points(log_dir, fio_object, start_end_times_list, fio_job_config, difference_tuple): 

    #Let's try rate-limiting to see how that effects start and end times.
    #print(log_dir)
    #print(fio_object)
    #print(start_end_times_list)
    old_fsync_value = difference_tuple[1]
    original_old_fsync_value = difference_tuple[1]
    new_fsync_value = -1

    minimum_time = min([tup[3] for tup in start_end_times_list])
    maximum_time = max([tup[3] for tup in start_end_times_list])
    difference = maximum_time - minimum_time
    difference_ratio = (maximum_time - minimum_time) / 140
    fsync_file_value = -1
    
    with open(fio_job_config, 'r') as file:
        for line in file:
            if 'fsync' in line:
                #old_fsync_value = int(re.split('=', line)[1])
                fsync_file_value = int(re.split('=', line)[1])
                if old_fsync_value == -1:
                    old_fsync_value = fsync_file_value
    if difference_ratio < 1 and difference_ratio > 0:
        #assert old_fsync_value == fsync_file_value
        if old_fsync_value == -1:
            print(f"SOMETHING WENT WRONG! fsync value in job file {fio_job_config} either not detected or is -1!")
        elif old_fsync_value <= 0:
            old_fsync_value = 1
        else:
            new_fsync_value = int(old_fsync_value * (1 - difference_ratio) - 1)

        if new_fsync_value <= 1 and not new_fsync_value == -1:
            new_fsync_value = 1

    print(f"Minimum time is {minimum_time}, and Maximum time is {maximum_time}. The difference between the maximum and minimum end times for this iteration is {difference}. It is {difference_ratio} of the job time. Old fsync value was {original_old_fsync_value} and new fsync value is {new_fsync_value}. fsync value in the file is {fsync_file_value} and old fsync value is {old_fsync_value}")
    return (difference_ratio, new_fsync_value)
