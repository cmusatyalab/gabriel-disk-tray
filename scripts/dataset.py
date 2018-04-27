import os
import pprint
import glob

import fire
import tensorflow as tf


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
                line_num = len(f.read().splitlines())
            stats[split][os.path.basename(data_file)] = line_num
    pprint.pprint(stats)


if __name__ == '__main__':
    fire.Fire()
