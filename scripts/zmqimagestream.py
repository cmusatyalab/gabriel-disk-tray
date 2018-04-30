# zmqimage.py -- classes to send, receive and display cv2 images via zmq
#     based on serialization in pyzmq docs and pyzmq/examples/serialization

'''
PURPOSE:
    These classes allow a headless (no display) computer running OpenCV code
    to display OpenCV images on another computer with a display.
    For example, a headless Raspberry Pi with no display can run OpenCV code
    and can display OpenCV images on a Mac with a display.
AUTHOR:
    Jeff Bass, https://github.com/jeffbass, jeff@yin-yang-ranch.com
    modified by junjuew
'''

import zmq
import numpy as np


class SerializingSocket(zmq.Socket):
    """A class with some extra serialization methods

    send_array sends numpy arrays with metadata necessary
    for reconstructing the array on the other side (dtype,shape).
    Also sends array name for display with cv2.show(image).

    recv_array receives dict(arrayname,dtype,shape) and an array
    and reconstructs the array with the correct shape and array name.
    """

    def send_array(self, A, arrayname="NoName", flags=0, copy=True, track=False):
        """send a numpy array with metadata and array name"""
        md = dict(
            arrayname=arrayname,
            dtype=str(A.dtype),
            shape=A.shape,
        )
        self.send_json(md, flags | zmq.SNDMORE)
        return self.send(A, flags, copy=copy, track=track)

    def recv_array(self, flags=0, copy=True, track=False):
        """recv a numpy array, including arrayname, dtype and shape"""
        md = self.recv_json(flags=flags)
        msg = self.recv(flags=flags, copy=copy, track=track)
        A = np.frombuffer(msg, dtype=md['dtype'])
        return (md['arrayname'], A.reshape(md['shape']))


class SerializingContext(zmq.Context):
    _socket_class = SerializingSocket


class zmqImageSender():
    '''A class that opens a zmq REQ socket on the headless computer
    '''

    def __init__(self, connect_to="tcp://jeff-mac:5555"):
        '''initialize zmq socket for sending images to display on remote computer'''
        '''connect_to is the tcp address:port of the display computer'''
        self.zmq_context = SerializingContext()
        self.zmq_socket = self.zmq_context.socket(zmq.REQ)
        self.zmq_socket.connect(connect_to)

    def imsend(self, arrayname, array, wait=True):
        '''send image to display on remote server'''
        if array.flags['C_CONTIGUOUS']:
            # if array is already contiguous in memory just send it
            self.zmq_socket.send_array(array, arrayname, copy=False)
        else:
            # else make it contiguous before sending
            array = np.ascontiguousarray(array)
            self.zmq_socket.send_array(array, arrayname, copy=False)
        # needed due to zmq REQ/REP paradigm
        if wait:
            message = self.zmq_socket.recv()


class zmqImageReceiver():
    '''A class that opens a zmq REP socket to receive images
    '''
    def __init__(self, open_port="tcp://*:5555"):
        '''initialize zmq socket on viewing computer that will display images'''
        self.zmq_context = SerializingContext()
        self.zmq_socket = self.zmq_context.socket(zmq.REP)
        self.zmq_socket.bind(open_port)

    def imrecv(self, copy=False):
        '''receive and show image on viewing computer display'''
        arrayname, image = self.zmq_socket.recv_array(copy=copy)
        return arrayname, image

    def imack(self):
        self.zmq_socket.send(b"OK")
