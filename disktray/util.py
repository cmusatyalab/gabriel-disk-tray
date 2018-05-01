from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import contextlib2
import os
import signal
import sys
import time
from logzero import logger


def set_up_exit_handler(cleanup_func):
    def exit_signal_handler(signal, frame):
        cleanup_func()
        sys.exit(0)

    signal.signal(signal.SIGINT, exit_signal_handler)


def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


class Timer(contextlib2.ContextDecorator):

    def __init__(self, name):
        self._name = name

    def __enter__(self):
        self._st = time.time()

    def __exit__(self, *args):
        self._et = time.time()
        logger.info('{} took {:.2f} ms'.format(self._name, (self._et - self._st) * 1000))