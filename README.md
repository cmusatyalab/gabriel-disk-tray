# Overview [![Docker Build Status](https://img.shields.io/docker/build/jamesjue/gabriel-disk-tray.svg)](https://hub.docker.com/r/jamesjue/gabriel-disk-tray)
Cognitive Assistance for assembling a disk tray.

# Installation
Please see [Dockerfile](Dockerfile) for details.

# How to Run
## Container
```bash
nvidia-docker run --rm -it --name disktray \
-p 0.0.0.0:9098:9098 -p 0.0.0.0:9111:9111 -p 0.0.0.0:22222:22222 \
-p 0.0.0.0:7070:7070 -p 0.0.0.0:8080:8080 \
-e "DISKTRAY_VIDEO_SERVER_URL=http://<server-public-ip-or-hostname>:8080"  \
jamesjue/gabriel-disk-tray:latest
```
## Source
  1. Set following environment variables
      1. DISKTRAY_FASTER_RCNN_ROOT
      2. DISKTRAY_VIDEO_SERVER_URL
  1. Start the Gabriel Control and Ucomm server
  ```bash
  docker run --rm --name gabriel -p 0.0.0.0:9098:9098 \
  -p 0.0.0.0:9111:9111 -p 0.0.0.0:22222:22222 -p 10120:10120 \
  -p 8021:8021 -p 9090:9090 -p 10101:10101 \
  jamesjue/gabriel /bin/bash -c \
  "gabriel-control -l -n eth0 & sleep 5; gabriel-ucomm -s 127.0.0.1:8021"
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
