from __future__ import print_function
import sys
import cv2 
import boto3
import time
#from pathlib import Path
import pandas as pd
#from botocore.exceptions import ClientError
#from IPython.display import display
import json
#import torch
import datetime
import pytz
import pickle
import numpy as np
from multiprocessing import Pool


default_capture_rate = 30
#model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # or yolov5n - yolov5x6, custom
sns_client = boto3.client('sns')
kinesis_client = boto3.client("kinesis")

def load_config():
    '''Load configuration from file.'''
    with open('../config/videocapture-params.json', 'r') as conf_file:
        conf_json = conf_file.read()
        return json.loads(conf_json)

#Send frame to Kinesis stream
#Send frame to Kinesis stream
def encode_and_send_frame(frame, frame_count, enable_kinesis=True, write_file=False):
    try:
        #convert opencv Mat to jpg image
        #print "----FRAME---"
        retval, buff = cv2.imencode(".jpg", frame)

        img_bytes = bytearray(buff)

        utc_dt = pytz.utc.localize(datetime.datetime.now())
        now_ts_utc = (utc_dt - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()

        frame_package = {
            'ApproximateCaptureTime' : now_ts_utc,
            'FrameCount' : frame_count,
            'ImageBytes' : img_bytes
        }

        if write_file:
            print("Writing file img_{}.jpg".format(frame_count))
            target = open("img_{}.jpg".format(frame_count), 'w')
            target.write(img_bytes)
            target.close()

        #put encoded image in kinesis stream
        if enable_kinesis:
            print("Sending image to Kinesis")
            response = kinesis_client.put_record(
                StreamName="FrameStream",
                Data=pickle.dumps(frame_package),
                PartitionKey="partitionkey"
            )
            print(response)

    except Exception as e:
        print(e)


def main ():

    config = load_config()
    phone_num = config.get("label_watch_phone_num", "")

    cam = cv2.VideoCapture(0)
    camera_msg = False
    ip_cam_url = "webcam"
    capture_rate = default_capture_rate
    argc = len(sys.argv)

    # read ip camera url and capture rate from command line arguments
    if argc > 1:
        ip_cam_url = sys.argv[1]

        if argc > 2 and sys.argv[2].isdigit():
            capture_rate = int(sys.argv[2])
    
    if (ip_cam_url != "webcam"):
        cam = cv2.VideoCapture(ip_cam_url)

    print("Capturing from '{}' at a rate of 1 every {} frames...".format(ip_cam_url, capture_rate))
    
    bytes = b''
    pool = Pool(processes=3)

    frame_count = 0
    while True:
        ret, frame = cam.read()

        if (camera_msg == False):
            sns_client.publish(PhoneNumber = phone_num, Message='Camera is active!' )
            camera_msg = True

        if ret:
            if frame_count % capture_rate == 0:
                result = pool.apply_async(encode_and_send_frame, (frame, frame_count, True, False,))

            frame_count += 1


            cv2.imshow("capturing",frame)
            #cv2.imshow('YOLO', np.squeeze(results.render()))
            # print("triggering yolov5")
            # img = frame  # or file, Path, PIL, OpenCV, numpy, list

            # # classes = None  # (optional list) filter by class, i.e. = [0, 15, 16] for COCO persons, cats and dogs
            
            # #print("time: ", time.time())
            # results = model(img)
            # #print("test print: ",results)
            # results.print()
            # #results.save()
            # results = results.pandas().xyxy[0]
            # display(results)

            # found = results[results['name'].str.contains('cat')]
            # num_cat = len(found)
            
            # if (num_cat > 0):
            #     print("found: ", num_cat," cats")
            #     sns_client.publish(PhoneNumber = phone_num, Message='Cat appeared ^-^!' )
            #     time.sleep(2)
            # labels = results.xyxyn[0][:,-1]
            # for i in labels:
            #     print(i)

            #counter = 0
            
            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            #counter += 1
    
    cam.release()
    cv2.destroyAllWindows()
    sns_client.publish(PhoneNumber = phone_num, Message='Camera is inactive!' )


if __name__ == '__main__':
    main()