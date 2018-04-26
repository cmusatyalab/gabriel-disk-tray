from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
import fire
from logzero import logger

import util
import zmqimagestream


def get_frame(cam):
    while True:
        ret_val, img = cam.read()
        if ret_val:
            yield img
        else:
            logger.debug("No More frames.")
            return


def start_streaming(camera_id, connect_to):
    streamer = zmqimagestream.zmqImageSender(connect_to=connect_to)
    cam = cv2.VideoCapture(camera_id)
    if not cam.isOpened():
        raise IOError("Failed to open camera.")
    cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 600)
    cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 400)

    def release_camera():
        cam.release()
        logger.info("Camera Released.")
    util.set_up_exit_handler(release_camera)

    for img in get_frame(cam):
        encoded_img = cv2.imencode('.jpg', img)[1]
        streamer.imsend("img", encoded_img)
        logger.debug("send one more frame")


if __name__ == '__main__':
    fire.Fire(start_streaming)
