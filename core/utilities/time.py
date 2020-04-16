import time


def get_local_time():
    return time.strftime("%B %d, %y %H:%M:%S", time.localtime())


def get_time_stamp():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())