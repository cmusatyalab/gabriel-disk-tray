#!/usr/bin/env python
#
# Object detection servers for using tensorflow models.
#
#   Author: Zhuo Chen <zhuoc@cs.cmu.edu>, Junjue Wang <junjuew@cs.cmu.edu>
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

import os
import struct
import sys
import threading
import time
import traceback

import cv2

if os.path.isdir("../../gabriel/server"):
    sys.path.insert(0, "../../gabriel/server")

import zmqimagestream
import tf_inference
import util
import gabriel

LOG = gabriel.logging.getLogger(__name__)

# ikea related
from disktray import config

sys.path.insert(0, "..")
from disktray import zhuocv as zc

config.setup(is_streaming=True)

LOG_TAG = "Ikea: "

display_list = config.DISPLAY_LIST


class IkeaProcessing(threading.Thread):
    def __init__(self):
        self.stop = threading.Event()
        experiment_dir = os.getenv('experiment_dir', None)
        export_dir = os.path.join(experiment_dir, 'exported')
        data_dir = os.path.join(experiment_dir, 'data')
        frozen_graph_path = os.path.join(export_dir, 'frozen_inference_graph.pb')
        label_file_path = os.path.join(data_dir, 'label_map.pbtxt')
        num_classes = 3
        self.tfmodel = tf_inference.TFModel(frozen_graph_path, label_file_path, num_classes)
        self.server = zmqimagestream.zmqImageReceiver(open_port=config.TF_TASK_BIND_URL)

        threading.Thread.__init__(self, target=self.run)

    def run(self):
        input_list = [self.server]
        output_list = []
        error_list = []

        LOG.info(LOG_TAG + "lamp processing thread started")
        try:
            while (not self.stop.wait(0.001)):
                _, encoded_img = self.server.imrecv()
                img = cv2.imdecode(encoded_img, cv2.CV_LOAD_IMAGE_UNCHANGED)
                LOG.info("recv one image")
                with util.Timer('TF detection') as t:
                    output_dict = self.tfmodel.run_inference_for_single_image(img)
                LOG.info("# of detected boxes: {}".format(output_dict['num_detections']))
                img = tf_inference.visualize_highest_prediction_per_class(img, output_dict, self.tfmodel.category_index)
                self.server.zmq_socket.send_json([])
                cv2.imshow('test', img)
                cv2.waitKey(25)
        except Exception as e:
            LOG.warning(LOG_TAG + traceback.format_exc())
            LOG.warning(LOG_TAG + "%s" % str(e))
            LOG.warning(LOG_TAG + "handler raises exception")
            LOG.warning(LOG_TAG + "Server is disconnected unexpectedly")
        LOG.debug(LOG_TAG + "ikea processing thread terminated")

    @staticmethod
    def _recv_all(socket, recv_size):
        data = ''
        while len(data) < recv_size:
            tmp_data = socket.recv(recv_size - len(data))
            if tmp_data == None or len(tmp_data) == 0:
                raise Exception("Socket is closed")
            data += tmp_data
        return data

    def _receive(self, sock):
        try:
            img_size = struct.unpack("!I", self._recv_all(sock, 4))[0]
            img = self._recv_all(sock, img_size)
        except Exception as e:
            return
        print(        "received one image"
        cv_img = zc.raw2cv_image(img)
        return_data = self._handle_img(cv_img)

        packet = struct.pack("!I%ds" % len(return_data), len(return_data), return_data)
        sock.sendall(packet)

    def _handle_img(self, img):
        ## preprocessing of input image
        resize_ratio = 1
        if max(img.shape) > config.IMAGE_MAX_WH:
            resize_ratio = float(config.IMAGE_MAX_WH) / max(img.shape[0], img.shape[1])
            img = cv2.resize(img, (0, 0), fx=resize_ratio, fy=resize_ratio, interpolation=cv2.INTER_AREA)
        zc.check_and_display('input', img, display_list, resize_max=config.DISPLAY_MAX_PIXEL,
                             wait_time=config.DISPLAY_WAIT_TIME)

        ## get current state
        rtn_msg, state = ic.process(img, resize_ratio, display_list)
        if state is None:
            return "None"

        return state

    def terminate(self):
        self.stop.set()


if __name__ == "__main__":
    # a thread to receive incoming images
    ikea_processing = IkeaProcessing()
    ikea_processing.start()
    ikea_processing.isDaemon = True

    try:
        while True:
            time.sleep(1)
    except Exception as e:
        pass
    except KeyboardInterrupt as e:
        sys.stdout.write("user exits\n")
    finally:
        if ikea_processing is not None:
            ikea_processing.terminate()
