# Disk Tray Cognitive Assistance [![Build Status][travis-image]][travis] [![Docker Image Status][docker-image]][docker] [![License][license-image]][license] [![Gitter][gitter-image]][gitter]

Cognitive assistance application for assembling a disk tray. In collaboration with the company [inwinSTACK](http://www.inwinstack.com/en/home/), we created a Gabriel application for training a new worker in disk tray assembly for a desktop.

[docker-image]: https://img.shields.io/docker/build/cmusatyalab/gabriel-disk-tray.svg
[docker]: https://hub.docker.com/r/cmusatyalab/gabriel-disk-tray

[travis-image]: https://travis-ci.org/cmusatyalab/gabriel-disk-tray.svg?branch=master
[travis]: http://travis-ci.org/cmusatyalab/gabriel-disk-tray

[license-image]: http://img.shields.io/badge/license-Apache--2-blue.svg?style=flat
[license]: LICENSE

[gitter-image]: https://badges.gitter.im/Join%20Chat.svg
[gitter]: https://gitter.im/gabriel-disk-tray/LOBBY

## Demo
This [video demo](https://www.youtube.com/watch?v=AwWZcL9XGI0) was shown live at the Computex 2018 show in Taiwan in June 2018.   The application was created by Junjue Wang of CMU, and demoed at Computex by inwinSTACK employees.   The small size of some of the components (especially the pin) and the precise nature of the assembly were difficult challenges to overcome in creating this application.  The wearable device used in this application is an ODG-7.

## Installation
### Client
An Android client is available on the Google PlayStore 

<a href='https://play.google.com/store/apps/details?id=edu.cmu.cs.gabrielclient'><img height='80px' width='120px' alt='Get it on Google Play' src='https://play.google.com/intl/en_us/badges/images/generic/en_badge_web_generic.png'/></a>

### Server
Running the server application using Docker is advised. If you want to install from source, please see [Dockerfile](Dockerfile) for details.


## How to Run
### Client
From the main activity one can add servers by name and IP/domain. Subtitles for audio feedback can also been toggled. This option is useful for devices that may not have integrated speakers(like ODG R-7).
Pressing the 'Play' button next to a server will initiate a connection to the Gabriel server at that address.

### Server
#### Container
```bash
nvidia-docker run --rm -it --name disktray \
-p 0.0.0.0:9098:9098 -p 0.0.0.0:9111:9111 -p 0.0.0.0:22222:22222 \
-p 0.0.0.0:7070:7070 -p 0.0.0.0:8080:8080 \
-e "DISKTRAY_VIDEO_SERVER_URL=http://<server-public-ip-or-hostname>:8080"  \
-e "DISKTRAY_DEMO_SHOW_ANNOTATED_IMAGE=True" \
jamesjue/gabriel-disk-tray:latest
```
#### Source
  1. Set following environment variables
      1. DISKTRAY_FASTER_RCNN_ROOT: root directory of [py-faster-rcnn](https://github.com/rbgirshick/py-faster-rcnn) installation.
      2. DISKTRAY_VIDEO_SERVER_URL: video feedback server url.
      3. DISKTRAY_DEMO_SHOW_ANNOTATED_IMAGE: True or False, whether to show annotated image stream on Gabriel Debug Website.
  1. Start the Gabriel Control and Ucomm server
  ```bash
  docker run --rm --name gabriel -p 0.0.0.0:9098:9098 \
  -p 0.0.0.0:9111:9111 -p 0.0.0.0:22222:22222 -p 10120:10120 \
  -p 8021:8021 -p 9090:9090 -p 10101:10101 \
  jamesjue/gabriel /bin/bash -c \
  "gabriel-control -l -d -n eth0 & sleep 5; gabriel-ucomm -s 127.0.0.1:8021"
  ```
  2. Download the asset file
  ```bash
  bash -e scripts/download_asset.sh
  ```
  2. Start the Video Instruction HTTP Server at the video feedback directory.
  ```bash
  cd feedbacks/video
  docker run -dit --name my-apache-app \
  -p 8080:80 -v "$PWD":/usr/local/apache2/htdocs/ httpd:2.4
  ```
  4. Run the DiskTray cognitive engine
  ```bash
  disktrayapp -s 127.0.0.1:8021
  ```
