import sys

from itertools import cycle

from settings import *
from utils.LoadBalancer import LoadBalancer
# from utils.loggers.Logger import Logger

from contextlib import redirect_stdout


if __name__ == '__main__':
    try:
        print('Started')
        LoadBalancer('localhost', 4001).start()
    except KeyboardInterrupt:
        print("Ctrl C - Stopping load_balancer")
        sys.exit(1)
