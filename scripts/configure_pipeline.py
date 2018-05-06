import os
import re

import fire
import tensorflow as tf
from logzero import logger


def get_tfrecord_data_num(file_path):
    cnt = 0
    for _ in tf.python_io.tf_record_iterator(file_path):
        cnt += 1
    return cnt


def configure_pipeline(num_classes, learning_rate, max_step,
                       fine_tune_checkpoint, data_dir, template_path, min_dimension=600, max_dimension=1070,
                       batch_size=5, max_detections_per_class=100, max_total_detections=300):
    """Configure a pipeline based on template.

    The output of the pipeline will be saved to data_dir.
    """
    with open(template_path) as f:
        template = f.read()
    template = re.sub('(?<=\s)num_classes: [0-9]+', 'num_classes: {}'.format(num_classes), template)
    template = re.sub('(?<=\s)min_dimension: [0-9]+', 'min_dimension: {}'.format(min_dimension), template)
    template = re.sub('(?<=\s)max_dimension: [0-9]+', 'max_dimension: {}'.format(max_dimension), template)
    template = re.sub('(?<=\s)batch_size: [0-9]+', 'batch_size: {}'.format(batch_size), template)
    template = re.sub('(?<=\s)max_detections_per_class: [0-9]+',
                      'max_detections_per_class: {}'.format(max_detections_per_class), template)
    template = re.sub('(?<=\s)max_total_detections: [0-9]*', 'max_total_detections: {}'.format(max_total_detections),
                      template)
    template = re.sub('(?<=\s)learning_rate: [0-9\.]+', 'learning_rate: {:f}'.format(learning_rate),
                      template)
    template = re.sub('(?<=\s)num_steps: [0-9]+', 'num_steps: {}'.format(max_step), template)
    template = re.sub('(?<=\s)fine_tune_checkpoint: ".*"',
                      'fine_tune_checkpoint: "{}"'.format(os.path.abspath(fine_tune_checkpoint)),
                      template)
    data_files = ['train.record', 'val.record', 'label_map.pbtxt']
    for data_file in data_files:
        template = re.sub(data_file, os.path.abspath(os.path.join(data_dir, data_file)), template)
    eval_data_file_path = os.path.join(data_dir, 'val.record')
    num_eval_data = get_tfrecord_data_num(eval_data_file_path)
    template = re.sub('(?<=\s)num_examples: [0-9]+',
                      'num_examples: {}'.format(num_eval_data),
                      template)
    template = re.sub('(?<=\s)num_visualizations: [0-9]+',
                      'num_visualizations: {}'.format(num_eval_data),
                      template)
    output_file_path = os.path.join(data_dir, 'pipeline.config')
    with open(output_file_path, 'w') as f:
        f.write(template)
    logger.debug(template)
    logger.info("pipeline file saved to {}".format(output_file_path))


if __name__ == '__main__':
    fire.Fire(configure_pipeline)
