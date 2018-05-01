#!/usr/bin/env python
#
# Cloudlet Infrastructure for Mobile Computing
#   - Task Assistance
#
#   Author: Zhuo Chen <zhuoc@cs.cmu.edu>
#
#   Copyright (C) 2011-2013 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2

from disktray import config

STATES = ["start", "nothing", "base", "pipe", "shade", "buckle", "blackcircle", "shadebase", "bulb", "bulbtop"]


class Task:
    def __init__(self):
        self.current_state = "start"

    def _check_dangling(self, objects):
        trays = []
        levers = []
        for i in xrange(objects.shape[0]):
            if int(objects[i, -1] + 0.1) == config.LABELS.index('tray'):
                trays.append(objects[i, :])
            if (int(objects[i, -1] + 0.1) == config.LABELS.index('lever')) or (int(objects[i, -1] + 0.1) ==
                                                                               config.LABELS.index('leverside')):
                levers.append(objects[i, :])

        assert len(trays) == 1
        assert len(levers) == 1
        tray = trays[0]
        lever = levers[0]

        correct_placmenet = False
        tray_center = ((tray[0] + tray[2]) / 2, (tray[1] + tray[3]) / 2)
        lever_center = ((lever[0] + lever[2]) / 2, (lever[1] + lever[3]) / 2)
        # the center of the lever to the left of the tray's quarter of width
        if abs(lever_center[0] - tray[0]) < 0.5 * abs(tray_center[0] - tray[0]):
            correct_placmenet = True
        return correct_placmenet

    @staticmethod
    def _set_instruction(result, speech, image_path, video_path):
        result['speech'] = speech
        image_path = image_path
        result['image'] = cv2.imread(image_path) if image_path else None
        if config.VIDEO_GUIDANCE:
            result['video'] = config.VIDEO_URL_PREFIX + video_path

    def get_instruction(self, objects):
        """
        Get instructions for the next state
        :param objects: [[x1, y1, x2, y2, confidence, cls_idx]]
        :return:
        """
        result = {'status': "success"}

        # the start
        if self.current_state == "start":
            result['speech'] = "Put the tray on the table."
            image_path = "images_feedback/tray.jpg"
            result['image'] = cv2.imread(image_path) if image_path else None
            self.current_state = "nothing"
            return result

        if len(objects) == 0:  # nothing detected
            return result

        # get the count of detected objects
        object_counts = {}
        for idx, object_name in enumerate(config.LABELS):
            object_counts[object_name] = sum(objects[:, -1] == idx)

        if self.current_state == "nothing":
            if object_counts['tray'] == 1:
                self._set_instruction(result, "Good job. Now show me the lever", "images_feedback/lever.jpg",
                                      "lever.mp4")
                self.current_state = "lever"
        elif self.current_state == "lever":
            if object_counts['lever'] == 1:
                self._set_instruction(result, "Good job. Now assemble the lever onto tray. Show me the vertical view.",
                                      "images_feedback/dangling.jpg",
                                      "dangling.mp4"
                                      )
                self.current_state = "dangling"
        elif self.current_state == "dangling":
            if object_counts['tray'] == 1 and (object_counts['lever'] == 1 or object_counts['leverside'] == 1):
                if self._check_dangling(objects):
                    self._set_instruction(result, "Find the cap and show me the side view with pin holding up",
                                          "images_feedback/cap.jpg",
                                          "cap.mp4"
                                          )
                    self.current_state = "cap"
                else:
                    self._set_instruction(result, "The lever is misplaced. Please make sure it is secure.",
                                          "images_feedback/dangling.jpg", "dangling.mp4")
        elif self.current_state == "cap":
            if object_counts['arc'] == 1 and object_counts['pin'] == 1:
                self._set_instruction(result, "Excellent. Now assemble the cap onto the tray. Start from left to "
                                             "right. Show "
                                      "me a vertical view when done", "images_feedback/assembled.jpg", "assembled.mp4")
                self.current_state = "assembled"
        elif self.current_state == "assembled":
            if object_counts['assembled'] == 1:
                self._set_instruction(result, "Awesome. Show me a close-up view to see if the pin is at right place.",
                                      "images_feedback/pin.jpg",
                                      "pin.mp4"
                                      )
                self.current_state = "pin"
        elif self.current_state == "pin":
            if object_counts['slotpin'] == 1:
                self._set_instruction(result, "Fabulous. Now close the lever.",
                                      "images_feedback/clamped.jpg", "clamped.mp4")
                self.current_state = "clamped"
            elif object_counts['pin'] == 1:
                self._set_instruction(result, "Please place the pin into the slot.", "images_feedback/pin.jpg",
                                      "correctpin.mp4")
        elif self.current_state == "clamped":
            if object_counts['clamped'] == 1:
                self._set_instruction(result, "Finished! Congraduations!", "images_feedback/finshed.jpg",
                                      "finished.mp4")

        if not config.VIDEO_GUIDANCE:
            if 'video' in result:
                del result['video']
        return result
