from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import signal
import sys
import time

import contextlib2
import numpy as np
from logzero import logger

from disktray import config


def set_up_exit_handler(cleanup_func):
    def exit_signal_handler(signal, frame):
        cleanup_func()
        sys.exit(0)

    signal.signal(signal.SIGINT, exit_signal_handler)


def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_sorted_objects_by_categories(self, objects, categories):
    cats_objs = []
    for cat in categories:
        cat_objs = self.get_objects_by_category(objects, cat)
        cats_objs.append(cat_objs)
    return np.vstack(cats_objs)


def get_sorted_objects_by_category(objects, category, object_list=config.LABELS):
    cat_objs = objects[np.where(objects[:, -1] == object_list.index(category))]
    # sort by confidence
    cat_objs[np.argsort(cat_objs[:, -2])[::-1]]
    return cat_objs


class Timer(contextlib2.ContextDecorator):

    def __init__(self, name):
        self._name = name

    def __enter__(self):
        self._st = time.time()

    def __exit__(self, *args):
        self._et = time.time()
        logger.info('{} took {:.2f} ms'.format(self._name, (self._et - self._st) * 1000))
