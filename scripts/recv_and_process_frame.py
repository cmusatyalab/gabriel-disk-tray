from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
import fire
from logzero import logger

import tf_inference
import util
import zmqimagestream


def start_receiving(frozen_graph_path, label_file_path, num_classes, listening_port, output_image_size=(6, 4)):
    tfmodel = tf_inference.TFModel(frozen_graph_path, label_file_path, num_classes)
    util.set_up_exit_handler(tfmodel.close)
    receiver = zmqimagestream.zmqImageReceiver(open_port=listening_port)
    while True:
        _, encoded_img = receiver.imrecv()
        img = cv2.imdecode(encoded_img, cv2.CV_LOAD_IMAGE_UNCHANGED)
        logger.debug("recv one image")
        with util.Timer('TF detection') as t:
            output_dict = tfmodel.run_inference_for_single_image(img)
        logger.debug("# of detected boxes: {}".format(output_dict['num_detections']))
        img = tf_inference.visualize_highest_prediction_per_class(img, output_dict, tfmodel.category_index,
                                                                  min_score_thresh=0.8)
        receiver.imack()
        cv2.imshow('test', img)
        cv2.waitKey(25)


if __name__ == '__main__':
    fire.Fire(start_receiving)
