import glob
import os

import fire
import numpy as np
import tensorflow as tf
from PIL import Image
from matplotlib import pyplot as plt
from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

if tf.__version__ < '1.4.0':
    raise ImportError('Please upgrade your tensorflow installation to v1.4.* or later!')


class TFModel(object):
    def __init__(self, frozen_graph_path, label_file_path, num_classes):
        self._frozen_graph_path = frozen_graph_path
        self._label_file_path = label_file_path
        self._num_classes = num_classes
        self._graph = self._load_graph(self._frozen_graph_path)
        self._category_index = self._load_label_map(self._label_file_path, self._num_classes)
        self._output_tensor_dict = self._get_inference_output_tensors(
            self._graph,
            ['num_detections', 'detection_boxes',
             'detection_scores', 'detection_classes',
             'detection_masks'])
        self._sess = tf.Session(graph=self._graph)

    @property
    def category_index(self):
        return self._category_index

    @staticmethod
    def _load_graph(frozen_graph_path):
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(frozen_graph_path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        return detection_graph

    @staticmethod
    def _load_label_map(label_file_path, num_classes):
        label_map = label_map_util.load_labelmap(label_file_path)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=num_classes,
                                                                    use_display_name=True)
        category_index = label_map_util.create_category_index(categories)
        return category_index

    @staticmethod
    def _get_inference_output_tensors(graph, tensor_list):
        tensor_dict = {}
        with graph.as_default():
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {output.name for op in ops for output in op.outputs}
            for key in tensor_list:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                        tensor_name)
        return tensor_dict

    def run_inference_for_single_image(self, image):
        """Run inference on a single image

        :param graph: Tensorflow graph with weights loaded
        :param output_tensor_dict: Dictionary of output tensor names to tensors
        :return: Inference results as a dictionary
        """
        output_tensor_dict = self._output_tensor_dict
        # Get handles to input and output tensors
        if 'detection_masks' in output_tensor_dict:
            # The following processing is only for single image
            detection_boxes = tf.squeeze(output_tensor_dict['detection_boxes'], [0])
            detection_masks = tf.squeeze(output_tensor_dict['detection_masks'], [0])
            # Reframe is required to translate mask from box coordinates to image coordinates and fit the
            # image size.
            real_num_detection = tf.cast(output_tensor_dict['num_detections'][0], tf.int32)
            detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
            detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
            detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                detection_masks, detection_boxes, image.shape[0], image.shape[1])
            detection_masks_reframed = tf.cast(
                tf.greater(detection_masks_reframed, 0.5), tf.uint8)
            # Follow the convention by adding back the batch dimension
            output_tensor_dict['detection_masks'] = tf.expand_dims(
                detection_masks_reframed, 0)
        image_tensor = self._graph.get_tensor_by_name('image_tensor:0')

        # Run inference
        output_dict = self._sess.run(output_tensor_dict,
                                     feed_dict={image_tensor: np.expand_dims(image, 0)})

        # all outputs are float32 numpy arrays, so convert types as appropriate
        output_dict['num_detections'] = int(output_dict['num_detections'][0])
        output_dict['detection_classes'] = output_dict[
            'detection_classes'][0].astype(np.uint8)
        output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
        output_dict['detection_scores'] = output_dict['detection_scores'][0]
        if 'detection_masks' in output_dict:
            output_dict['detection_masks'] = output_dict['detection_masks'][0]
        return output_dict

    def close(self):
        self._sess.close()
        print("tensorflow session closed.")


def load_image_into_numpy_array(image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)


def run_inference_on_test_dir(frozen_graph_path, label_file_path, num_classes, test_dir, output_image_size=(12, 8)):
    tfmodel = TFModel(frozen_graph_path, label_file_path, num_classes)
    test_image_paths = glob.glob(os.path.join(test_dir, '*'))
    for image_path in test_image_paths:
        image = Image.open(image_path)
        # the array based representation of the image will be used later in order to prepare the
        # result image with boxes and labels on it.
        image_np = load_image_into_numpy_array(image)
        # Actual detection.
        output_dict = tfmodel.run_inference_for_single_image(image_np)
        # Visualization of the results of a detection.
        vis_util.visualize_boxes_and_labels_on_image_array(
            image_np,
            output_dict['detection_boxes'],
            output_dict['detection_classes'],
            output_dict['detection_scores'],
            tfmodel.category_index,
            instance_masks=output_dict.get('detection_masks'),
            use_normalized_coordinates=True,
            line_thickness=8)
        plt.figure(figsize=output_image_size)
        plt.imshow(image_np)


if __name__ == '__main__':
    fire.Fire()
