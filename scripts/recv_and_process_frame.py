from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
import fire
import numpy as np
from object_detection.utils import visualization_utils as vis_util

import tf_inference
import util
import zmqimagestream


def get_frame(cam):
    while True:
        ret_val, img = cam.read()
        if ret_val:
            yield img
        else:
            return


def start_receiving(frozen_graph_path, label_file_path, num_classes, listening_port, output_image_size=(6, 4)):
    tfmodel = tf_inference.TFModel(frozen_graph_path, label_file_path, num_classes)
    util.set_up_exit_handler(tfmodel.close)
    receiver = zmqimagestream.zmqImageReceiver(open_port=listening_port)
    while True:
        _, img = receiver.imrecv(copy=True)
        print("recv one image")
        output_dict = tfmodel.run_inference_for_single_image(img)
        # Visualization of the results of a detection.
        img = np.copy(img)
        print("finished detection")
        vis_util.visualize_boxes_and_labels_on_image_array(
            img,
            output_dict['detection_boxes'],
            output_dict['detection_classes'],
            output_dict['detection_scores'],
            tfmodel.category_index,
            instance_masks=output_dict.get('detection_masks'),
            use_normalized_coordinates=True,
            line_thickness=8)
        receiver.imack()
        cv2.imshow('test', img)
        cv2.waitKey(25)


if __name__ == '__main__':
    fire.Fire(start_receiving)
