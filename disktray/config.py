# Copyright (C) 2018 Carnegie Mellon University. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Application wide configuration file."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from distutils.spawn import find_executable

# If True, configurations are set to process video stream in real-time (use with proxy.py)
# If False, configurations are set to process one independent image (use with debug.py)
IS_STREAMING = True

# Pure state detection or generate feedback as well
RECOGNIZE_ONLY = False

# Port for communication between proxy and task server
OBJECT_DETECTION_BINARY_PATH = find_executable('objectserver.py')
TASK_SERVER_IP = "127.0.0.1"
TASK_SERVER_PORT = 2722

# DEMO Related Setup
DEMO_SHOW_ANNOTATED_IMAGE = bool(os.getenv("DISKTRAY_DEMO_SHOW_ANNOTATED_IMAGE", False))

# Configs for object detection
USE_GPU = True

# Whether or not to save the displayed image in a temporary directory
SAVE_IMAGE = False

# Threshold for computer vision module
CONFIDENCE_THRESHOLD = 0.7
NMS_THRESHOLD = 0.3

# Whether to use video or image feedback
IMAGE_GUIDANCE = False
IMAGE_PATH_PREFIX = "feedback/images"
VIDEO_GUIDANCE = True
VIDEO_SERVER_URL = os.getenv('DISKTRAY_VIDEO_SERVER_URL')
if VIDEO_GUIDANCE and (VIDEO_SERVER_URL is None or len(VIDEO_SERVER_URL) == 0):
    raise ValueError(
        'DISKTRAY_VIDEO_SERVER_URL({}) environment variable not specified or not valid!'.format(VIDEO_SERVER_URL))

# Max image width and height
IMAGE_MAX_WH = 640

# ssh X Display flags. Better to use gabriel's debug webserver
# To see annotated input stream with detected object, use 'object'
DISPLAY_MAX_PIXEL = 400
DISPLAY_SCALE = 1
DISPLAY_LIST_ALL = []
DISPLAY_LIST_TEST = []
DISPLAY_LIST_STREAM = []
DISPLAY_LIST_TASK = []

# Used for cvWaitKey
DISPLAY_WAIT_TIME = 1 if IS_STREAMING else 500

# py-faster-rcnn based Object Detection Server
FASTER_RCNN_ROOT = os.getenv('DISKTRAY_FASTER_RCNN_ROOT')
if FASTER_RCNN_ROOT is None:
    raise ValueError('DISKTRAY_FASTER_RCNN_ROOT environment variable is not set. Please set it to be the path of '
                     'py-faster-rcnn package.')
MODEL_DIR = 'model'
if not os.path.exists(MODEL_DIR):
    raise ValueError('Model directory ({}) does not exist'.format(os.path.abspath(MODEL_DIR)))
with open('model/labels.txt', 'r') as f:
    content = f.read().splitlines()
    LABELS = content


def setup(is_streaming):
    global IS_STREAMING, DISPLAY_LIST, DISPLAY_WAIT_TIME, SAVE_IMAGE
    IS_STREAMING = is_streaming
    if not IS_STREAMING:
        DISPLAY_LIST = DISPLAY_LIST_TEST
    else:
        if RECOGNIZE_ONLY:
            DISPLAY_LIST = DISPLAY_LIST_STREAM
        else:
            DISPLAY_LIST = DISPLAY_LIST_TASK
    DISPLAY_WAIT_TIME = 1 if IS_STREAMING else 500
    SAVE_IMAGE = not IS_STREAMING
