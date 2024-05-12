'''
This lambda function fetches frames from Kinesis stream and performs object detection using the YoloV8 library.
Then it notifies watches and stores frames in S3 and DynamoDB
'''

import boto3
# from __future__ import print_function
import base64
import time
from decimal import Decimal
import uuid
import json
import pickle
from io import BytesIO
from PIL import Image
from pytz import timezone
from copy import deepcopy
from yolo_onnx.yolov8_onnx import YOLOv8

def load_config(path):
    '''Load configuration from file.'''
    with open(path, 'r') as conf_file:
        conf_json = conf_file.read()
        return json.loads(conf_json)
    
# Initialize YOLOv8 object detector
yolov8_detector = YOLOv8('./yolov8n.onnx')

#Initialize clients
sns_client = boto3.client('sns')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def process_image_handler(event, context):

    # Load config and set vars
    config = load_config("process_image_config.json")
    size = config['size']
    conf_thres = float(config["conf_thres"])
    iou_thres = float(config['iou_thres'])
    
    # Process frames fetched from Kinesis
    for record in event['Records']:

        frame_package_b64 = record['kinesis']['data']
        frame_package = pickle.loads(base64.b64decode(frame_package_b64))

        img_bytes = frame_package["ImageBytes"]
        capture_timestamp = frame_package["ApproximateCaptureTime"]
        frame_count = frame_package["FrameCount"]

        # open image
        img = Image.open(BytesIO(base64.b64decode(img_bytes.encode('ascii'))))

        try:
            # Infer results
            detections = yolov8_detector(img, size=size, conf_thres=conf_thres, iou_thres=iou_thres)
            print(detections)
        except Exception as e:
            print("An error occured:", e)
            return

process_image_handler({
  "key1": "value1",
  "key2": "value2",
  "key3": "value3"
}, None)