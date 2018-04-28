# To Run Inference
```bash
# server
python recv_and_process_frame.py $experiment_dir/exported/frozen_inference_graph.pb $experiment_dir/data/label_map.pbtxt 3 "tcp://*:5555"

# client
python send_camera_stream.py 0 "tcp://localhost:5555"
```
