from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import signal
import sys


def set_up_exit_handler(cleanup_func):
    def exit_signal_handler(signal, frame):
        cleanup_func()
        sys.exit(0)
    signal.signal(signal.SIGINT, exit_signal_handler)


