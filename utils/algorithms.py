from itertools import cycle
from settings import *


def round_robin(iter):
    return next(iter)


def least_conn(cache):
    try:
        next = min(cache, key=cache.get)
        if cache[next] == None:
            cache[next] = 1
        else:
            cache[next] = cache[next]+1
    except Exception as e:
        print('@'*50, e, '@'*50)
    return next


def weighted_least_conn():
    pass


def weighted_round_robin():
    pass
