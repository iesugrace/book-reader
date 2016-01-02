from time import *

def isotime(second):
    """
    return the iso time string from a second
    """
    return strftime('%Y-%m-%d %H:%M:%S', localtime(second))

def stddate(second):
    """
    return the date string of format '%Y-%m-%d'
    """
    return strftime('%Y-%m-%d', localtime(second))

def isostrtosecond(timestr):
    """
    return the second from an iso time string
    """
    return int(mktime(strptime(timestr, '%Y-%m-%d %H:%M:%S')))

def strtosecond(timestr):
    """
    valid formats of timestr:
    14:09
    14:09:01
    2015-06-15
    2015-06-15 14:09
    2015-06-15 14:09:01
    """
    # this function adds the 'second' part if omitted
    def complete_time(timestr):
        if len(timestr.split(':')) == 2:
            timestr += ':00'
        return timestr

    arr = timestr.split(' ')
    arr[-1] = complete_time(arr[-1])

    # only date or time is supplied, but not both
    if len(arr) == 1:
        if '-' in timestr:  # it is a date string
            arr.append('00:00:00')
        else:               # it is a time string, prepend the current date
            arr.insert(0, strftime('%Y-%m-%d'))

    timestr = ' '.join(arr)
    return isostrtosecond(timestr)

