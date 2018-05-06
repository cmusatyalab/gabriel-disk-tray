from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import hashlib
import io
import os
import pprint

from logzero import logger
import PIL.Image
import PIL.ImageDraw
import fire
import pascal_voc_writer
import tensorflow as tf
from lxml import etree
from object_detection.utils import dataset_util, label_map_util

import util


def read_image_file(file_path):
    with tf.gfile.GFile(file_path, 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = PIL.Image.open(encoded_jpg_io)
    if image.format != 'JPEG':
        raise ValueError('Image format not JPEG')
    return image


def read_tfrecord_file(file_path, debug=False):
    num = 0
    for example in tf.python_io.tf_record_iterator(file_path):
        result = tf.train.Example.FromString(example)
        if debug:
            if len(result.features.feature['image/object/class/text'].bytes_list.value) > 1:
                import pdb;
                pdb.set_trace()
        num += 1
    print("{} has {} items.".format(file_path, num))


def visualize_pascal_dataset(data_dir, output_dir):
    image_subdirectory = ''
    examples_path = os.path.join(data_dir, 'ImageSets', 'Main', 'train' + '.txt')
    annotations_dir = os.path.join(data_dir, 'Annotations')
    examples_list = dataset_util.read_examples_list(examples_path)
    for idx, example in enumerate(examples_list):
        path = os.path.join(annotations_dir, example + '.xml')
        with tf.gfile.GFile(path, 'r') as fid:
            xml_str = fid.read()
            xml = etree.fromstring(xml_str)
            data = dataset_util.recursive_parse_xml_to_dict(xml)['annotation']
            img_path = os.path.join(data['folder'], image_subdirectory, data['filename'])
            full_path = os.path.join(data_dir, img_path)
            image = read_image_file(full_path)
            width = int(data['size']['width'])
            height = int(data['size']['height'])
            assert width == image.size[0]
            assert height == image.size[1]

            if 'object' in data:
                for obj in data['object']:
                    xmin = float(obj['bndbox']['xmin'])
                    ymin = float(obj['bndbox']['ymin'])
                    xmax = float(obj['bndbox']['xmax'])
                    ymax = float(obj['bndbox']['ymax'])
                    classes_text = obj['name']
                    draw = PIL.ImageDraw.Draw(image)
                    draw.rectangle(((xmin, ymin), (xmax, ymax)), fill=None, outline='blue')
                    draw.text((xmin, ymin), classes_text)
                    del draw
            image.save(os.path.join(output_dir, os.path.basename(img_path)), 'JPEG')
            image.close()


def get_dataset_stats(dataset_dir):
    imageset_dir = os.path.abspath(os.path.join(dataset_dir, 'ImageSets', 'Main'))

    splits = {'train': '*train.txt', 'val': 'val.txt'}
    stats = {}
    for split, split_file_pattern in splits.items():
        split_files = glob.glob(os.path.join(imageset_dir, split_file_pattern))

        stats[split] = {}
        for data_file in split_files:
            with open(data_file) as f:
                content = f.read().splitlines()
                line_num = len(content)
                # specific to TPOD exported Pascal Dataset
                video_names = set(['_'.join(line.split('_')[:-1]) for line in content])
            stats[split][os.path.basename(data_file)] = {'# examples': line_num, 'videos': video_names}
    pprint.pprint(stats)


def pascalvoc_dict_to_tf_example(data,
                                 dataset_directory,
                                 label_map_dict,
                                 ignore_difficult_instances=False,
                                 image_subdirectory=''):
    """Convert XML derived dict to tf.Example proto.

    Notice that this function normalizes the bounding box coordinates provided
    by the raw data.

    Args:
      data: dict holding PASCAL XML fields for a single image (obtained by
        running dataset_util.recursive_parse_xml_to_dict)
      dataset_directory: Path to root directory holding PASCAL dataset
      label_map_dict: A map from string label names to integers ids.
      ignore_difficult_instances: Whether to skip difficult instances in the
        dataset  (default: False).
      image_subdirectory: String specifying subdirectory within the
        PASCAL dataset directory holding the actual image data.

    Returns:
      example: The converted tf.Example.

    Raises:
      ValueError: if the image pointed to by data['filename'] is not a valid JPEG
    """
    img_path = os.path.join(data['folder'], image_subdirectory, data['filename'])
    full_path = os.path.join(dataset_directory, img_path)
    with tf.gfile.GFile(full_path, 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = PIL.Image.open(encoded_jpg_io)
    if image.format != 'JPEG':
        raise ValueError('Image format not JPEG')
    key = hashlib.sha256(encoded_jpg).hexdigest()

    width = int(data['size']['width'])
    height = int(data['size']['height'])

    xmin = []
    ymin = []
    xmax = []
    ymax = []
    classes = []
    classes_text = []
    truncated = []
    poses = []
    difficult_obj = []
    if 'object' in data:
        for obj in data['object']:
            difficult = bool(int(obj['difficult']))
            if ignore_difficult_instances and difficult:
                continue

            difficult_obj.append(int(difficult))

            xmin.append(float(obj['bndbox']['xmin']) / width)
            ymin.append(float(obj['bndbox']['ymin']) / height)
            xmax.append(float(obj['bndbox']['xmax']) / width)
            ymax.append(float(obj['bndbox']['ymax']) / height)
            classes_text.append(obj['name'].encode('utf8'))
            classes.append(label_map_dict[obj['name']])
            truncated.append(int(obj['truncated']))
            poses.append(obj['pose'].encode('utf8'))

    example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(
            data['filename'].encode('utf8')),
        'image/source_id': dataset_util.bytes_feature(
            data['filename'].encode('utf8')),
        'image/key/sha256': dataset_util.bytes_feature(key.encode('utf8')),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature('jpeg'.encode('utf8')),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmin),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmax),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymin),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymax),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
        'image/object/difficult': dataset_util.int64_list_feature(difficult_obj),
        'image/object/truncated': dataset_util.int64_list_feature(truncated),
        'image/object/view': dataset_util.bytes_list_feature(poses),
    }))
    return example


def create_tf_record_from_pascalvoc_dataset(data_dir, label_map_path, output_path, set='train',
                                            annotations_dir='Annotations',
                                            ignore_difficult_instances=False):
    """
    Convert TPOD datasets in pascal format to TFRecord for object_detection.
    :param data_dir: Root directory to raw PASCAL VOC dataset.
    :param label_map_path: Path to label map proto
    :param output_path: Path to output TFRecord
    :param set: Convert training set, validation set or merged set.
    :param annotations_dir: (Relative) path to annotations directory.
    :param ignore_difficult_instances: Whether to ignore difficult instances
    :return:
    """
    SETS = ['train', 'val', 'trainval', 'test']
    if set not in SETS:
        raise ValueError('set must be in : {}'.format(SETS))

    data_dir = data_dir
    writer = tf.python_io.TFRecordWriter(output_path)
    label_map_dict = label_map_util.get_label_map_dict(label_map_path)

    tf.logging.info('labels: {}'.format(label_map_dict))

    examples_path = os.path.join(data_dir, 'ImageSets', 'Main', set + '.txt')
    annotations_dir = os.path.join(data_dir, annotations_dir)
    examples_list = dataset_util.read_examples_list(examples_path)
    for idx, example in enumerate(examples_list):
        if idx % 100 == 0:
            tf.logging.info('On image %d of %d', idx, len(examples_list))
        path = os.path.join(annotations_dir, example + '.xml')
        with tf.gfile.GFile(path, 'r') as fid:
            xml_str = fid.read()
        xml = etree.fromstring(xml_str)
        data = dataset_util.recursive_parse_xml_to_dict(xml)['annotation']

        tf_example = pascalvoc_dict_to_tf_example(data, data_dir, label_map_dict,
                                                  ignore_difficult_instances)
        writer.write(tf_example.SerializeToString())
    writer.close()


def create_pascalvoc_negative_dataset(image_dir, output_dir):
    """Create a pascal VOC dataset from image_dir without any annotations to serve as negative examples."""
    output_dir = os.path.abspath(output_dir)
    annotation_dir = os.path.join(output_dir, 'Annotations')
    imageset_dir = os.path.join(output_dir, 'ImageSets', 'Main')
    jpegimage_dir = os.path.join(output_dir, 'JPEGImages')
    directories = [output_dir, annotation_dir, imageset_dir, jpegimage_dir]
    for directory in directories:
        util.create_directory_if_not_exists(directory)

    # create annotation files
    for image_path in glob.glob(os.path.join(image_dir, '*.jpg')):
        image_file_name = os.path.basename(image_path)
        image = PIL.Image.open(image_path)
        output_image_path = os.path.join(jpegimage_dir, image_file_name)
        image.save(output_image_path)
        logger.info('{} --> {}'.format(image_path, output_image_path))
        width, height = image.size
        writer = pascal_voc_writer.Writer(output_image_path, width, height, database='negatives')
        # temporary fix to make folder to be relative
        writer.template_parameters['path'] = os.path.relpath(writer.template_parameters['path'], output_dir)
        annotation_file_path = os.path.join(annotation_dir, '{}.xml'.format(os.path.splitext(image_file_name)[0]))
        writer.save(annotation_file_path)
        image.close()
        logger.info('{} --> {}'.format(image_path, annotation_file_path))

    # create imageset train file
    image_file_names = [os.path.splitext(os.path.basename(image_path))[0] for image_path in glob.glob(os.path.join(
        image_dir, '*.jpg'))]
    with open(os.path.join(imageset_dir, 'train.txt'), 'w') as f:
        f.write('\n'.join(image_file_names))


if __name__ == '__main__':
    fire.Fire()
