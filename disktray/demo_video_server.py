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
"""Demo Video Player Server.

This video server receives an url of a video instruction and opens the video up in a web-browser. This is video
server is used in demos to let audience see what the wearable device is showing to the user.
"""
import socket
import struct
import sys
import threading
import time
import webbrowser

import gabriel

LOG = gabriel.logging.getLogger(__name__)


class VideoHandler(gabriel.network.CommonHandler):
    def setup(self):
        super(VideoHandler, self).setup()

    def __repr__(self):
        return "Video Server"

    def handle(self):
        LOG.info("New Ikea app connected")
        super(VideoHandler, self).handle()

    def _handle_input_data(self):
        # receive data
        data_size = struct.unpack("!I", self._recv_all(4))[0]
        data = self._recv_all(data_size)
        LOG.info('received {}'.format(data))
        webbrowser.open(data)

    def terminate(self):
        LOG.info("Pingpong app disconnected")
        super(VideoHandler, self).terminate()


class VideoServer(gabriel.network.CommonServer):
    def __init__(self, port, handler):
        gabriel.network.CommonServer.__init__(self, port, handler)  # cannot use super because it's old style class
        LOG.info("* Video server(%s) configuration" % str(self.handler))
        LOG.info(" - Open TCP Server at %s" % (str(self.server_address)))
        LOG.info(" - Disable nagle (No TCP delay)  : %s" %
                 str(self.socket.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)))
        LOG.info("-" * 50)

    def terminate(self):
        gabriel.network.CommonServer.terminate(self)


def main():
    video_server = VideoServer(5699, VideoHandler)
    video_thread = threading.Thread(target=video_server.serve_forever)
    video_thread.daemon = True

    try:
        video_thread.start()
        while True:
            time.sleep(100)
    except KeyboardInterrupt as e:
        sys.stdout.write("Exit by user\n")
        video_server.terminate()
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        video_server.terminate()
        sys.exit(1)
    else:
        video_server.terminate()
        sys.exit(0)


if __name__ == '__main__':
    main()
