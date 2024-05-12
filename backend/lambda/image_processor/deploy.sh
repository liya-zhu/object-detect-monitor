#!/bin/bash

# Remove existing deployment package
rm -f deployment_package.zip

# Change directory to the package folder
cd package

# Create a zip archive of the package folder and save it at the parent directory
zip -r ../deployment_package.zip .

# Change directory back to the original location
cd ..

# Add specific files to the deployment package
zip -u deployment_package.zip process_image* yolov8n.onnx 

# Change permissions of the deployment package
chmod 755 deployment_package.zip

# Copy the deployment package to S3 bucket
aws s3 cp deployment_package.zip s3://image-processor-lambda-src
