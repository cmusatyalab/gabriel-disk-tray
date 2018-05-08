# Copyright (C) 2018 Carnegie Mellon University. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Detect Objects using DNNs implemented in Caffe."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import matplotlib

matplotlib.use('Agg')

import json
import numpy as np
import os
import sys
import time

from disktray import config
sys.path.append(os.path.join(config.FASTER_RCNN_ROOT, "tools"))
# needed to intialize paths required by faster-rcnn
import _init_paths
# use _init_paths, just to make sure pycharm doesn't remove the _init_paths imports
# when reformatting code
with open(os.devnull, 'w') as f:
    f.write('py-faster-rcnn is initilialized. {}'.format(_init_paths.caffe_path))
from fast_rcnn.config import cfg as faster_rcnn_config
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms

sys.path.append(os.path.join(config.FASTER_RCNN_ROOT, "python"))
import caffe
from disktray import zhuocv as zc

current_milli_time = lambda: int(round(time.time() * 1000))

# initialize caffe module
faster_rcnn_config.TEST.HAS_RPN = True  # Use RPN for proposals
prototxt = os.path.join(config.MODEL_DIR, 'faster_rcnn_test.pt')
caffemodel = os.path.join(config.MODEL_DIR, 'model.caffemodel')

if not os.path.isfile(caffemodel):
    raise IOError(('{:s} not found.').format(caffemodel))

if config.USE_GPU:
    caffe.set_mode_gpu()
    # 0 is the default GPU ID
    caffe.set_device(0)
    faster_rcnn_config.GPU_ID = 0
else:
    caffe.set_mode_cpu()

net = caffe.Net(prototxt, caffemodel, caffe.TEST)

# Warmup on a dummy image
img = 128 * np.ones((300, 500, 3), dtype=np.uint8)
for i in range(2):
    _, _ = im_detect(net, img)


# img will be modified in this function
def detect_object(img, resize_ratio=1, confidence_threshold=0.5, nms_threshold=0.3):
    global net
    if config.USE_GPU:
        caffe.set_mode_gpu()
    else:
        caffe.set_mode_cpu()

    scores, boxes = im_detect(net, img)

    result = None
    for cls_idx in xrange(len(config.LABELS)):
        cls_idx += 1  # because we skipped background
        cls_boxes = boxes[:, 4 * cls_idx: 4 * (cls_idx + 1)]
        cls_scores = scores[:, cls_idx]

        # dets: detected results, each line is in [x1, y1, x2, y2, confidence] format
        dets = np.hstack((cls_boxes, cls_scores[:, np.newaxis])).astype(np.float32)

        # non maximum suppression
        keep = nms(dets, nms_threshold)
        dets = dets[keep, :]

        # filter out low confidence scores
        inds = np.where(dets[:, -1] >= confidence_threshold)[0]
        dets = dets[inds, :]

        # now change dets format to [x1, y1, x2, y2, confidence, cls_idx]
        dets = np.hstack((dets, np.ones((dets.shape[0], 1)) * (cls_idx - 1)))

        # combine with previous results (for other classes)
        if result is None:
            result = dets
        else:
            result = np.vstack((result, dets))

    if result is not None:
        result[:, :4] /= resize_ratio

    return (img, result)


def process(img, confidence_threshold, nms_threshold, resize_ratio=1, display_list=[]):
    img_object, result = detect_object(img, resize_ratio, confidence_threshold=confidence_threshold,
                                       nms_threshold=nms_threshold)
    rtn_msg = {'status': 'success'}
    return (rtn_msg, json.dumps(result.tolist()))
