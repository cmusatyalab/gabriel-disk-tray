#!/usr/bin/env python3
"""Create resource tarball, including trained DNN models and feedback media files and upload it to storage server."""
import os
import subprocess
import tarfile

import boto
import boto.s3.connection
import configparser
from logzero import logger


def _make_tarfile(output_filename, file_and_dir_list):
    with tarfile.open(output_filename, 'w:gz', dereference=True) as tar:
        for item in file_and_dir_list:
            tar.add(item)


def create_asset_tarball():
    asset_file_list = [
        'model/model.caffemodel',
        'model/faster_rcnn_test.pt',
        'model/labels.txt',
        'feedbacks/images',
        'feedbacks/videos'
    ]
    output_file = 'asset.tgz'
    if os.path.exists(output_file):
        os.remove(output_file)
    _make_tarfile(output_file, asset_file_list)
    return output_file


def upload_to_storage_server(host, access_key, secret_key, bucket_name, key_name, file_path):
    conn = boto.connect_s3(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        host=host,
        is_secure=True,
        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
    )

    bucket = conn.get_bucket(bucket_name)

    if not bucket:
        logger.debug('Bucket {} does not exist. Creating...'.format(bucket_name))
        bucket = conn.create_bucket(bucket_name)
        bucket.add_user_grant('FULL_CONTROL', 'backup')
        logger.debug('Creation finished.')

    logger.debug('uploading {} to {} under key {}'.format(file_path, host, key_name))
    key = bucket.new_key(key_name)
    key.set_contents_from_filename(file_path)
    key.set_canned_acl('public-read')


def md5(file_path):
    p = subprocess.run(["md5sum", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.cmusatyalab'))
    host = config['DEFAULT']['s3_host']
    access_key = config['DEFAULT']['s3_access_key']
    secret_key = config['DEFAULT']['s3_secret_key']
    file_path = create_asset_tarball()
    logger.debug('Creating asset file to {}'.format(file_path))
    upload_to_storage_server(host, access_key, secret_key, 'gabriel-model', 'disktray', file_path)
    logger.debug('upload finished! Remember to update the md5 hash in the documentation.')
    md5sum = md5(file_path)
    logger.info('The md5sum for {} is: {}'.format(file_path, md5sum))
