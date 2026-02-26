import os, sys
from statistics import mean, stdev

def log_and_analyze_data_points(log_dir, fio_object, start_end_times_list): 

    #Let's try rate-limiting to see how that effects start and end times.
    #print(log_dir)
    #print(fio_object)
    #print(start_end_times_list)
    durations = []

    durations = [end - start for _, _, start, end in start_end_times_list]
    mu = mean(durations)
    if len(durations) > 1:
        sigma = stdev(durations)

        # Calculating coefficient of variation which is standard deviation divided by the average
        cv = sigma / mu

        print("Minimum duration is: {}, Maximum duration is: {}, Standard deviation is: {}, mean is: {}, Coefficient of variance is: {}".format(min(durations), max(durations), sigma, mu, cv))
        if cv > .04:
            #file_contents = file_contents.replace("__fsync__", new_fsync_value)
            return cv
    return False

