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

import Queue
import copy
import json
import multiprocessing
import pprint
import socket
import struct
import sys
import time
from base64 import b64encode

import cv2
import gabriel
import gabriel.proxy
import numpy as np

from disktray import config
from disktray import task
from disktray import zhuocv as zc

LOG = gabriel.logging.getLogger(__name__)

config.setup(is_streaming=True)

display_list = config.DISPLAY_LIST_TASK

LOG_TAG = "DiskTray Proxy: "


def reorder_objects(result):
    # build a mapping between faster-rcnn recognized object order to a standard order
    object_mapping = [-1] * len(config.LABELS)
    with open("model/labels.txt") as f:
        lines = f.readlines()
        for idx, line in enumerate(lines):
            line = line.strip()
            object_mapping[idx] = config.LABELS.index(line)

    for i in xrange(result.shape[0]):
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


class DiskTrayApp(gabriel.proxy.CognitiveProcessThread):
    def __init__(self, image_queue, output_queue, task_server_addr, engine_id, log_flag=True):
        super(DiskTrayApp, self).__init__(image_queue, output_queue, engine_id)
        self.log_flag = log_flag
        self.is_first_image = True
        self._previous_instruction = {}
        self._previous_instruction_timestamp = time.time()
        # minimum time interval between two duplicate instructions are given
        self._min_time_interval_between_duplicate_instructions = 20

        # task initialization
        self.task = task.Task()

        # GPU machine offloaded part
        try:
            self.task_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.task_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.task_server_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.task_server_sock.connect(task_server_addr)
            LOG.info(LOG_TAG + "connected to task server")
        except socket.error as e:
            LOG.warning(LOG_TAG + "Failed to connect to task server at %s" % str(task_server_addr))

    def terminate(self):
        if self.task_server_sock is not None:
            self.task_server_sock.close()
        super(DiskTrayApp, self).terminate()

    @staticmethod
    def _recv_all(socket, recv_size):
        data = ''
        while len(data) < recv_size:
            tmp_data = socket.recv(recv_size - len(data))
            if tmp_data == None or len(tmp_data) == 0:
                raise gabriel.proxy.ProxyError("Socket is closed")
            data += tmp_data
        return data

    def _remove_duplicate_instructions(self, current_result):
        """Remove duplicate instructions to avoid flooding an user with a huge amount of same instructions"""
        # ignore the results that do not have any instructions
        if 'speech' not in current_result and 'image' not in current_result and 'video' not in current_result:
            return current_result

        elapsed_time = time.time() - self._previous_instruction_timestamp
        next_previous_result = copy.copy(current_result)
        if elapsed_time < self._min_time_interval_between_duplicate_instructions:
            if current_result == self._previous_instruction:
                LOG.info('Duplicated instructions! Removing speech, image and video instructions from {}'.format(
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

    def handle(self, header, data):
        # receive data from control VM
        LOG.info("received new image")

        header['status'] = "nothing"
        result = {}  # default

        # preprocessing of input image
        img = zc.raw2cv_image(data)
        zc.check_and_display('input', img, display_list, resize_max=config.DISPLAY_MAX_PIXEL,
                             wait_time=config.DISPLAY_WAIT_TIME)

        # get object detection result
        # feed data to the task assistance app
        packet = struct.pack("!I%ds" % len(data), len(data), data)
        self.task_server_sock.sendall(packet)
        result_size = struct.unpack("!I", self._recv_all(self.task_server_sock, 4))[0]
        objects_data = self._recv_all(self.task_server_sock, result_size)

        # the object detection result format is, for each line: [x1, y1, x2, y2, confidence, cls_idx]
        objects = np.array(json.loads(objects_data))
        objects = reorder_objects(objects)
        LOG.info("object detection result: %s" % objects)

        # for measurement, when the sysmbolic representation has been got
        if gabriel.Debug.TIME_MEASUREMENT:
            header[gabriel.Protocol_measurement.JSON_KEY_APP_SYMBOLIC_TIME] = time.time()

        # get instruction based on state
        instruction, control = self.task.get_instruction(objects)
        if instruction['status'] != 'success':
            return json.dumps(result)

        # suppress duplicate instructions
        self._remove_duplicate_instructions(instruction)

        # display annotated image if needed
        if "object" in display_list:
            self._show_annotated_image(img, objects)

        # return annotated image for demo display if needed
        if config.DEMO_SHOW_ANNOTATED_IMAGE:
            self._replace_instruction_image_with_annotated_image(img, objects, instruction)

        # send instructions back to client or the demo servers
        header['status'] = 'success'
        if instruction.get('speech', None) is not None:
            result['speech'] = instruction['speech']
            display_verbal_guidance(result['speech'])
        if instruction.get('image', None) is not None:
            feedback_image = b64encode(zc.cv_image2raw(instruction['image']))
            result['image'] = feedback_image
        if instruction.get('video', None) is not None:
            result['video'] = instruction['video']

        # send sensor control back
        if control:
            header[gabriel.Protocol_client.JSON_KEY_CONTROL_MESSAGE] = json.dumps(control)
        return json.dumps(result)

    @staticmethod
    def _show_annotated_image(img, objects):
        img_object = zc.vis_detections(img, objects, config.LABELS)
        zc.check_and_display("object", img_object, display_list, resize_max=config.DISPLAY_MAX_PIXEL,
                             wait_time=config.DISPLAY_WAIT_TIME)

    @staticmethod
    def _replace_instruction_image_with_annotated_image(img, objects, instruction):
        img_object = zc.vis_detections(img, objects, config.LABELS)
        instruction['image'] = img_object


def main():
    settings = gabriel.util.process_command_line(sys.argv[1:])

    ip_addr, port = gabriel.network.get_registry_server_address(settings.address)
    service_list = gabriel.network.get_service_list(ip_addr, port)
    LOG.info("Gabriel Server :")
    LOG.info(pprint.pformat(service_list))

    video_ip = service_list.get(gabriel.ServiceMeta.VIDEO_TCP_STREAMING_IP)
    video_port = service_list.get(gabriel.ServiceMeta.VIDEO_TCP_STREAMING_PORT)
    ucomm_ip = service_list.get(gabriel.ServiceMeta.UCOMM_SERVER_IP)
    ucomm_port = service_list.get(gabriel.ServiceMeta.UCOMM_SERVER_PORT)

    # object detection
    object_detection_process = gabriel.proxy.AppLauncher(config.OBJECT_DETECTION_BINARY_PATH, is_print=True)
    object_detection_process.start()
    object_detection_process.isDaemon = True
    time.sleep(15)

    # image receiving thread
    image_queue = Queue.Queue(gabriel.Const.APP_LEVEL_TOKEN_SIZE)
    LOG.info("TOKEN SIZE OF OFFLOADING ENGINE: %d" % gabriel.Const.APP_LEVEL_TOKEN_SIZE)
    video_streaming = gabriel.proxy.SensorReceiveClient((video_ip, video_port), image_queue)
    video_streaming.start()
    video_streaming.isDaemon = True

    # app proxy
    result_queue = multiprocessing.Queue()

    task_server_ip = config.TASK_SERVER_IP
    task_server_port = config.TASK_SERVER_PORT
    app_proxy = DiskTrayApp(image_queue, result_queue, (task_server_ip, task_server_port), engine_id="DiskTray")
    app_proxy.start()
    app_proxy.isDaemon = True

    # result pub/sub
    result_pub = gabriel.proxy.ResultPublishClient((ucomm_ip, ucomm_port), result_queue)
    result_pub.start()
    result_pub.isDaemon = True

    try:
        while True:
            time.sleep(1)
    except Exception as e:
        pass
    except KeyboardInterrupt as e:
        sys.stdout.write("user exits\n")
    finally:
        if video_streaming is not None:
            video_streaming.terminate()
        if app_proxy is not None:
            app_proxy.terminate()
        if object_detection_process is not None:
            object_detection_process.terminate()
        result_pub.terminate()
