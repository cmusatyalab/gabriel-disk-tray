import os
import pprint
import glob
import re

import fire
from logzero import logger
import tensorflow as tf


def get_tfrecord_data_num(file_path):
    cnt = 0
    for _ in tf.python_io.tf_record_iterator(file_path):
        cnt += 1
    return cnt


def configure_pipeline(num_classes, learning_rate, max_step,
                       fine_tune_checkpoint, data_dir, template_path, min_dimension=600, max_dimension=1070,
                       batch_size=5):
    """Configure a pipeline based on template.

    The output of the pipeline will be saved to data_dir.
    """
    with open(template_path) as f:
        template = f.read()
    template = re.sub('num_classes: [0-9]*', 'num_classes: {}'.format(num_classes), template)
    template = re.sub('min_dimension: [0-9]*', 'min_dimension: {}'.format(min_dimension), template)
    template = re.sub('max_dimension: [0-9]*', 'max_dimension: {}'.format(max_dimension), template)
    template = re.sub('batch_size: [0-9]*', 'batch_size: {}'.format(batch_size), template)
    template = re.sub('initial_learning_rate: [0-9\.]*', 'initial_learning_rate: {:f}'.format(learning_rate),
                      template)
    template = re.sub('num_steps: [0-9]*', 'num_steps: {}'.format(max_step), template)
    template = re.sub('fine_tune_checkpoint: ".*"',
                      'fine_tune_checkpoint: "{}"'.format(os.path.abspath(fine_tune_checkpoint)),
                      template)
    data_files = ['train.record', 'val.record', 'label_map.pbtxt']
    for data_file in data_files:
        template = re.sub(data_file, os.path.abspath(os.path.join(data_dir, data_file)), template)
    eval_data_file_path = os.path.join(data_dir, 'val.record')
    template = re.sub('num_examples: [0-9]*', 'num_examples: {}'.format(get_tfrecord_data_num(eval_data_file_path)),
                      template)
    output_file_path = os.path.join(data_dir, 'pipeline.config')
    with open(output_file_path, 'w') as f:
        f.write(template)
    logger.debug(template)
    logger.info("pipeline file saved to {}".format(output_file_path))


if __name__ == '__main__':
    fire.Fire(configure_pipeline)
