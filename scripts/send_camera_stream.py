from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
import fire

import util
import zmqimagestream


def get_frame(cam):
    while True:
        ret_val, img = cam.read()
        if ret_val:
            yield img
        else:
            print("No More frames.")
            return


def start_streaming(camera_id, connect_to):
    streamer = zmqimagestream.zmqImageSender(connect_to=connect_to)
    cam = cv2.VideoCapture(camera_id)

    util.set_up_exit_handler(cam.release)

    for img in get_frame(cam):
        streamer.imsend("img", img)
        print("send one more frame")


if __name__ == '__main__':
    fire.Fire(start_streaming)
