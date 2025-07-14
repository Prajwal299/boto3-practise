# ec2_creator.py

import boto3
import os
import sys
import time

# --- CONFIGURATION ---
AWS_REGION = 'eu-north-1'
AMI_ID = 'ami-042b4708b1d05f512'  # Ubuntu 22.04 LTS for eu-north-1
INSTANCE_TYPE = 't3.micro'
SECURITY_GROUP_ID = 'sg-0cd0055363c2a2d75' # IMPORTANT: Ensure this SG allows inbound traffic on port 5000 (for Flask) and 22 (for SSH)

# The name we will give our temporary key pair and the local file to save it in.
KEY_NAME = 'jenkins-temp-boto3-key'
KEY_FILE_PATH = f'{KEY_NAME}.pem'

GIT_REPO_URL = 'https://github.com/Prajwal299/boto3-practise.git'

# --- EC2 UserData Script ---
user_data_script = f"""#!/bin/bash
# Wait for apt to be ready
while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
   sleep 5
done

# Update and install necessary packages
apt-get update -y
apt-get install -y docker.io git

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Clone the Flask app project
cd /home/ubuntu
git clone {GIT_REPO_URL}

# Navigate into the correct directory
cd boto3-practise/flask-app-3

# Build the Docker image
docker build -t flask-app-3 .

# Run the Docker container
docker run -d -p 5000:5000 --name my-flask-container flask-app-3
"""

print("--- Starting EC2 Instance Deployment ---")

session = boto3.Session(region_name=AWS_REGION)
ec2_client = session.client('ec2')

try:
    # --- Step 1: Create EC2 Key Pair ---
    print(f"Creating new EC2 Key Pair named: {KEY_NAME}")
    
    # To make the script re-runnable, delete the key pair if it exists from a previous failed run
    try:
        ec2_client.delete_key_pair(KeyName=KEY_NAME)
        print(f"Deleted existing key pair '{KEY_NAME}' to ensure a clean run.")
    except ec2_client.exceptions.ClientError as e:
        if "InvalidKeyPair.NotFound" in str(e):
            pass # This is expected if the key doesn't exist
        else:
            raise # Re-raise other unexpected errors

    key_pair_response = ec2_client.create_key_pair(KeyName=KEY_NAME)
    
    # --- Step 2: Save the Private Key to a local .pem file ---
    private_key_material = key_pair_response['KeyMaterial']
    with open(KEY_FILE_PATH, 'w') as key_file:
        key_file.write(private_key_material)
    
    # On Linux/macOS, we must set the file permissions. Not required for Windows, but good practice.
    if os.name == 'posix':
        os.chmod(KEY_FILE_PATH, 0o400)
    
    print(f"Successfully saved private key to '{KEY_FILE_PATH}'")

    # --- Step 3: Launch EC2 instance using the new key ---
    print("Launching EC2 instance...")
    response = ec2_client.run_instances(
        ImageId=AMI_ID,
        MinCount=1,
        MaxCount=1,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,  # Using the key we just created
        SecurityGroupIds=[SECURITY_GROUP_ID],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': 'Jenkins-Flask-App-Deploy'}]
            }
        ],
        UserData=user_data_script
    )

    instance_id = response['Instances'][0]['InstanceId']
    print(f"Successfully initiated launch for instance: {instance_id}")

    # --- Step 4: Wait for Instance to be Running ---
    ec2_resource = session.resource('ec2')
    instance = ec2_resource.Instance(instance_id)

    print("Waiting for instance to enter 'running' state...")
    instance.wait_until_running()
    instance.reload()

    print("Instance is now running.")
    print(f"Public IP Address: {instance.public_ip_address}")
    print(f"--> Access your Flask app at: http://{instance.public_ip_address}:5000")
    print("Deployment seems successful. The temporary key will now be deleted.")

except Exception as e:
    print(f"An ERROR occurred during deployment: {e}")
    # Exit with a non-zero status code to make the Jenkins job fail
    sys.exit(1)

finally:
    # --- Step 5: Clean Up Resources ---
    # This block will run whether the script succeeds or fails
    print("--- Starting Cleanup ---")
    
    # Delete the EC2 Key Pair from AWS
    try:
        ec2_client.delete_key_pair(KeyName=KEY_NAME)
        print(f"Successfully deleted key pair '{KEY_NAME}' from AWS.")
    except Exception as e:
        print(f"Could not delete key pair '{KEY_NAME}' from AWS. You may need to delete it manually. Error: {e}")

    # Delete the local .pem file
    if os.path.exists(KEY_FILE_PATH):
        os.remove(KEY_FILE_PATH)
        print(f"Successfully deleted local key file '{KEY_FILE_PATH}'.")
    
    print("--- Cleanup Complete ---")