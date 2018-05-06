# To Run Inference
```bash
# server
python recv_and_process_frame.py $experiment_dir/exported/frozen_inference_graph.pb $experiment_dir/data/label_map.pbtxt 3 "tcp://*:5555"

# client
python send_camera_stream.py 0 "tcp://localhost:5555"
```

# Running the Training Job

A local training job can be run with the following command:

```bash
# From the tensorflow/models/research/ directory
python object_detection/train.py \
    --logtostderr \
    --pipeline_config_path=$experiment_dir/data/pipeline.config \
    --train_dir=$experiment_dir/models/model/train
```
# Running the Evaluation Job
```bash
# From the tensorflow/models/research/ directory
python object_detection/eval.py \
    --logtostderr \
    --pipeline_config_path=$experiment_dir/data/pipeline.config \
    --checkpoint_dir=$experiment_dir/models/model/train \
    --eval_dir=$experiment_dir/models/model/eval
```

# Running Tensorboard

```bash
tensorboard --logdir=$experiment_dir/models/model
```

# Export Trained Model
```bash
python object_detection/export_inference_graph.py --input_type image_tensor --pipeline_config_path $experiment_dir/data/pipeline.config  --trained_checkpoint_prefix $experiment_dir/models/model/train/model.ckpt --output_directory $experiment_dir/exported
```
