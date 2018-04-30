from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import io
import os
import pprint

import PIL.Image
import PIL.ImageDraw
import fire
import tensorflow as tf
from lxml import etree
from object_detection.utils import dataset_util


def read_image_file(file_path):
    with tf.gfile.GFile(file_path, 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = PIL.Image.open(encoded_jpg_io)
    if image.format != 'JPEG':
        raise ValueError('Image format not JPEG')
    return image


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


if __name__ == '__main__':
    fire.Fire()
