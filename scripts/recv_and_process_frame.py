from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
import fire
import numpy as np
from logzero import logger
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


def visualize_highest_prediction_per_class(img, output_dict, category_index, min_score_thresh=0.5):
    # find the highest scored boxes
    detection_boxes = []
    detection_classes = []
    detection_scores = []
    detected_classes = set(output_dict['detection_classes'].tolist())
    # find the highest scored box by class
    for cls_idx in detected_classes:
        idx_in_detection_array = np.where(output_dict['detection_classes'] == cls_idx)[0]
        idx_to_score = {idx: output_dict['detection_scores'][idx] for idx in idx_in_detection_array}
        # sorted indices from highest scores to lowest
        sorted_idx_by_score = zip(*sorted(idx_to_score.items(), key=lambda (idx, score): (score, idx),
                                          reverse=True))[0]
        # choose top 1
        top_idx_by_score = np.array(sorted_idx_by_score[:1])
        cls_detection_boxes = output_dict['detection_boxes'][top_idx_by_score]
        cls_detection_classes = output_dict['detection_classes'][top_idx_by_score]
        cls_detection_scores = output_dict['detection_scores'][top_idx_by_score]
        detection_boxes.extend(cls_detection_boxes)
        detection_classes.extend(cls_detection_classes)
        detection_scores.extend(cls_detection_scores)

    # Visualization of the results of a detection.
    vis_util.visualize_boxes_and_labels_on_image_array(
        img,
        np.array(detection_boxes),
        np.array(detection_classes),
        np.array(detection_scores),
        category_index,
        min_score_thresh=min_score_thresh,
        instance_masks=output_dict.get('detection_masks'),
        use_normalized_coordinates=True,
        line_thickness=8)
    return img


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
        img = visualize_highest_prediction_per_class(img, output_dict, tfmodel.category_index)
        receiver.imack()
        cv2.imshow('test', img)
        cv2.waitKey(25)


if __name__ == '__main__':
    fire.Fire(start_receiving)
