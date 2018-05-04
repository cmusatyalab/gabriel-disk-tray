# Overview
Cognitive Asssistance for assembling a disk tray.

# Dependencies

Espeak

# To Run
  * Start the Gabriel Control and Ucomm server
  ```bash
  docker run --rm --name gabriel -p 0.0.0.0:9098:9098 \
  -p 0.0.0.0:9111:9111 -p 0.0.0.0:22222:22222 -p 10120:10120 \
  -p 8021:8021 -p 9090:9090 -p 10101:10101 \
  jamesjue/gabriel /bin/bash -c \
  "gabriel-control -l -n eth0 & sleep 5; gabriel-ucomm -s 127.0.0.1:8021"
  ```
  * Start the Video Instruction HTTP Server at the video feedback dir.
  ```bash
  cd feedbacks/video
  docker run -dit --name my-apache-app \
  -p 8080:80 -v "$PWD":/usr/local/apache2/htdocs/ httpd:2.4
  ```
  * Start the video and sound server when doing the demo
  * Run the DiskTray cognitive engine
  ```bash
  python disktray/disktray.py
  ```
