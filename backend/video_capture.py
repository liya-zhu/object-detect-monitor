'''
This module captures frames from a web-cam or IP camera and sends it to Kinesis stream
'''
import argparse
import pickle
from datetime import datetime
import cv2
import boto3
from multiprocessing import Pool
import pytz

kinesis_client = boto3.client("kinesis")
sns_client = boto3.client('sns')

# Set capture parameters
CAPTURE_RATE = 30

def send_frame(frame, frame_count):
    '''
    Sends frames to Kinesis stream for processing and displaying
    '''
    try:
        # Convert frame to jpg image
        retval, buffer = cv2.imencode(".jpg", frame)
        image_bytes = bytearray(buffer)

        frame_package = {
            'CaptureTime' : datetime.now(pytz.utc),
            'FrameCount' : frame_count,
            'ImageBytes' : image_bytes
        }

        # Send image to Kinesis stream
        print("Sending image to Kinesis")
        response = kinesis_client.put_record(
            StreamName = "object-detect-stream",
            Data = pickle.dumps(frame_package), # serialize into a binary
            PartitionKey = "partitionkey"
        )
        print("Kinesis response:", response)

    except Exception as e:
        print("An error occured:", e)


def main():
    # Read command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--camera", choices=['web', 'ip'], default='web', help="Choose camera source", required=True)
    parser.add_argument("-u", "--url", help="IP camera url")
    parser.add_argument("-n", "--number", help="Phone number to send message to", required=True)
    args = parser.parse_args()
    
    camera_source = 0 # default to webcam
    phone_num = args.number

    if args.camera == 'ip':
        if not args.url:
            print("Please specify ip camera url when 'ip' is selected as the camera source.")
            return
        camera_source = args.url
        print(f"Capturing from '{camera_source}' at a rate of 1 of every {CAPTURE_RATE} frames.")
    else:
        print(f"Capturing from web cam at a rate of 1 of every {CAPTURE_RATE} frames.")

    capture = cv2.VideoCapture(camera_source)
    pool = Pool(processes=3)

    print("Notifying", phone_num)
    sns_client.publish(PhoneNumber = phone_num, Message='Activating camera' )

    frame_count = 0
    while True:
        # Capture frame-by-frame
        ret, frame = capture.read()

        #cv2.resize(frame, (640, 360));

        if ret is False:
            break

        if frame_count % CAPTURE_RATE == 0:
            pool.apply_async(send_frame, (frame, frame_count))

        frame_count += 1

        # Display the resulting frame
        cv2.imshow('Captured Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the capture object, destory windows, and send message to notify user
    capture.release()
    cv2.destroyAllWindows()
    print("Notifying", phone_num)
    sns_client.publish(PhoneNumber = phone_num, Message='Deactivating camera' )

    return

if __name__ == '__main__':
    main()