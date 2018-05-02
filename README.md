# Overview
Cognitive Asssistance for assembling a disk tray.

# Dependencies

Gabriel, espeak

# To Run
  * Start the Video Instruction HTTP Server at the video feedback dir.
  ```bash
  cd feedbacks/video
  docker run -dit --name my-apache-app \
  -p 8080:80 -v "$PWD":/usr/local/apache2/htdocs/ httpd:2.4
  ```
