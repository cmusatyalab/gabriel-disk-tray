#!/usr/bin/env python
#
# Cloudlet Infrastructure for Mobile Computing
#   - Task Assistance
#
#   Author: Zhuo Chen <zhuoc@cs.cmu.edu>
#
#   Copyright (C) 2011-2013 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# If True, configurations are set to process video stream in real-time (use with proxy.py)
# If False, configurations are set to process one independent image (use with debug.py)
import os

IS_STREAMING = True

# Pure state detection or generate feedback as well
RECOGNIZE_ONLY = False

# Port for communication between proxy and task server
OBJECT_DETECTION_BINARY_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'objectserver.py')
TASK_SERVER_IP = "128.2.211.75"
TASK_SERVER_PORT = 2722

# DEMO Related Setup
# Play video
PLAY_VIDEO = True
# Port for video server
DEMO_VIDEO_SERVER = ("128.2.213.185", 5699)
# Play sound
PLAY_SOUND = True
# Port for sound server
DEMO_SOUND_SERVER = ("128.2.213.185", 4299)

TF_TASK_SERVER_URL = "tcp://localhost:5555"
TF_TASK_BIND_URL = "tcp://*:5555"

# Configs for object detection
USE_GPU = True

# Whether or not to save the displayed image in a temporary directory
SAVE_IMAGE = False

# Threshold for computer vision module
CONFIDENCE_THRESHOLD = 0.7
NMS_THRESHOLD = 0.3

# Whether to use video or image feedback
IMAGE_PATH_PREFIX = "feedback/images"
VIDEO_GUIDANCE = True
VIDEO_URL_PREFIX = "http://sandstorm.elijah.cs.cmu.edu:8080/"

# Max image width and height
IMAGE_MAX_WH = 640

# Display
DISPLAY_MAX_PIXEL = 400
DISPLAY_SCALE = 1
DISPLAY_LIST_ALL = ['input', 'object']
DISPLAY_LIST_TEST = ['input', 'object']
DISPLAY_LIST_STREAM = []
DISPLAY_LIST_TASK = ['input', 'object', 'text_guidance']

# Used for cvWaitKey
DISPLAY_WAIT_TIME = 1 if IS_STREAMING else 500

# The objects(states) which can be detected
with open('model/labels.txt', 'r') as f:
    content = f.read().splitlines()
    LABELS = content

# The parameters for locating the hologram feedback
holo_pos_paras = {'pipe': [17500, 0.5, 0.45],
                  'lettuce': [6500, 0.5, 0.32],
                  'bread': [7000, 0.5, 0.3],
                  'tomato': [7500, 0.5, 0.26],
                  'breadtop': [7800, 0.5, 0.22]}


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
