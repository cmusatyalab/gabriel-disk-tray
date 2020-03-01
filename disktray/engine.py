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
"""DiskTray Cognitive Assistance Application."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
import queue
import copy
import json
import logging
import multiprocessing
import pprint
import socket
import struct
import sys
import time
from base64 import b64encode

import cv2
import numpy as np

from gabriel_server import cognitive_engine
from gabriel_protocol import gabriel_pb2

from disktray import config
from distray import instruction_pb2
from disktray import task
from disktray import zhuocv as zc

logger = logging.getLogger(__name__)

config.setup(is_streaming=True)

display_list = config.DISPLAY_LIST_TASK
ENGINE_NAME = "instruction"
LOG_TAG = "DiskTray Proxy: "


def reorder_objects(result):
    # build a mapping between faster-rcnn recognized object order to a standard order
    object_mapping = [-1] * len(config.LABELS)
    with open("model/labels.txt") as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            object_mapping[idx] = config.LABELS.index(line)

    for i in range(result.shape[0]):
        result[i, -1] = object_mapping[int(result[i, -1] + 0.1)]

    return result


def display_verbal_guidance(text):
    img_display = np.ones((200, 400, 3), dtype=np.uint8) * 100
    lines = text.split('.')
    y_pos = 30
    for line in lines:
        cv2.putText(img_display, line.strip(), (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, [0, 255, 0])
        y_pos += 50
    zc.check_and_display('text_guidance', img_display, display_list, resize_max=config.DISPLAY_MAX_PIXEL,
                         wait_time=config.DISPLAY_WAIT_TIME)


class DiskTrayEngine(cognitive_engine.Engine):
    def __init__(self, cpu_only):
        super(DiskTrayEngine, self).__init__()
        self.is_first_image = True
        self._previous_instruction = {}
        self._previous_instruction_timestamp = time.time()
        # minimum time interval between two duplicate instructions are given
        self._min_time_interval_between_duplicate_instructions = 20

        # task initialization
        self.task = task.Task()

    def _remove_duplicate_instructions(self, current_result):
        """Remove duplicate instructions to avoid flooding an user with a huge amount of same instructions"""
        # ignore the results that do not have any instructions
        if 'speech' not in current_result and 'image' not in current_result and 'video' not in current_result:
            return current_result

        elapsed_time = time.time() - self._previous_instruction_timestamp
        next_previous_result = copy.copy(current_result)
        if elapsed_time < self._min_time_interval_between_duplicate_instructions:
            if current_result == self._previous_instruction:
                logger.info('Duplicated instructions! Removing speech, image and video instructions from {}'.format(
                    current_result))
                current_result.pop('speech', None)
                current_result.pop('image', None)
                current_result.pop('video', None)
            else:
                self._previous_instruction_timestamp = time.time()
        else:
            self._previous_instruction_timestamp = time.time()
        self._previous_instruction = next_previous_result
        return current_result

    def _detect_object(self, img):
        # TODO detect object using  code from caffedetect.py
        return None

    def handle(self, from_client):
        if from_client.payload_type != gabriel_pb2.PayloadType.IMAGE:
            return cognitive_engine.wrong_input_format_error(
                from_client.frame_id)

        result = {}  # default

        engine_fields = cognitive_engine.unpack_engine_fields(
        instruction_pb2.EngineFields, from_client)

        img_array = np.asarray(bytearray(from_client.payload), dtype=np.int8)
        img = cv2.imdecode(img_array, -1)


        if max(img.shape) > config.IMAGE_MAX_WH:
            resize_ratio = float(config.IMAGE_MAX_WH) / max(img.shape[0], img.shape[1])

            img = cv2.resize(img, (0, 0), fx=resize_ratio, fy=resize_ratio,
                             interpolation=cv2.INTER_AREA)
            objects = self._detect_object(img)
            if objects is not None:
                objects[:, :4] /= resize_ratio
        else:
            objects = self._detect_object(img)


        # the object detection result format is, for each line: [x1, y1, x2, y2, confidence, cls_idx]
        objects = reorder_objects(objects)
        logger.info("object detection result: %s" % objects)

        # get instruction based on state
        instruction, control = self.task.get_instruction(objects)        
        if control:
            logger.warn("Sensor control is set, but not being returned in this version.")

        if instruction['status'] != 'success':
            logger.error(json.dumps(result))
            result_wrapper = gabriel_pb2.ResultWrapper()
            result_wrapper.engine_fields.Pack(engine_fields)
            result_wrapper.status = gabriel_pb2.ResultWrapper.Status.ENGINE_ERROR
            return result_wrapper

        # suppress duplicate instructions
        self._remove_duplicate_instructions(instruction)

        # instruction = {'status': 'success' 
        # [, 'speech': <str>] 
        # [, 'image': path<str>]
        # [, 'video': path<str>] }}

        # send instructions back to client
        if 'speech' in instruction or 'image' in instruction:
            engine_fields.update_count += 1
            result_wrapper = gabriel_pb2.ResultWrapper()
            result_wrapper.engine_fields.Pack(engine_fields)
            result = gabriel_pb2.ResultWrapper.Result()
            result.payload_type = gabriel_pb2.PayloadType.IMAGE
            result.engine_name = ENGINE_NAME
            with open(instruction['image'], 'rb') as f:
                result.payload = f.read()
            result_wrapper.results.append(result)

            result = gabriel_pb2.ResultWrapper.Result()
            result.payload_type = gabriel_pb2.PayloadType.TEXT
            result.engine_name = ENGINE_NAME
            result.payload = instruction['speech'].encode(encoding="utf-8")
            result_wrapper.results.append(result)
        else: # no update
            result_wrapper = gabriel_pb2.ResultWrapper()
            result_wrapper.engine_fields.Pack(engine_fields)

        result_wrapper.frame_id = from_client.frame_id
        result_wrapper.status = gabriel_pb2.ResultWrapper.Status.SUCCESS

        return result_wrapper
    
