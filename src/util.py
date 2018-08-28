''' Generic Utility Functions '''

from datetime import datetime


def measure_task(task, label, count=10, print_every_time=False):
    ''' utility for measuring the computation time of given function task, which takes index as argument '''
    times = []
    for i in range(count):
        before = datetime.now()
        task(i)
        elapsed = datetime.now() - before
        seconds_elapsed = elapsed.seconds + elapsed.microseconds / 1000000.0
        times.append(seconds_elapsed)
        if print_every_time:
            print('Time to %s: %.3fs' % (label, seconds_elapsed))

    avg_time = sum(times) / float(len(times))
    print('Average time to %s: %.3fs' % (label, avg_time))
