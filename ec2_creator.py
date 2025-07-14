# ec2_creator.py

import boto3
import os
import sys
import time
import paramiko # New dependency for SSH
import socket

# --- CONFIGURATION ---
AWS_REGION = 'eu-north-1'
AMI_ID = 'ami-042b4708b1d05f512'  # Ubuntu 22.04 LTS for eu-north-1
INSTANCE_TYPE = 't3.micro'
SECURITY_GROUP_ID = 'sg-0cd0055363c2a2d75' # IMPORTANT: Ensure this SG allows inbound traffic on port 22 (for SSH) and 5000 (for Flask)

KEY_NAME = 'jenkins-boto3-persistent-key'
KEY_FILE_PATH = f'{KEY_NAME}.pem'

GIT_REPO_URL = 'https://github.com/Prajwal299/boto3-practise.git'

# --- List of commands to be executed remotely ---
# We will run these over SSH after the instance is up
REMOTE_COMMANDS = [
    "sudo apt-get update -y",
    "sudo apt-get install -y docker.io git",
    "sudo systemctl start docker",
    "sudo systemctl enable docker",
    "sudo usermod -aG docker ubuntu", # Note: This takes effect on next login. The current session will still need sudo for docker.
    f"git clone {GIT_REPO_URL} /home/ubuntu/boto3-practise",
    "cd /home/ubuntu/boto3-practise/flask-app-3",
    "sudo docker build -t flask-app-3 .",
    "sudo docker run -d -p 5000:5000 --name my-flask-container flask-app-3"
]

print("--- Starting EC2 Instance Deployment ---")

session = boto3.Session(region_name=AWS_REGION)
ec2_client = session.client('ec2')

# --- Helper function to execute commands remotely ---
def execute_remote_command(ssh_client, command):
    print(f"--- Executing: {command} ---")
    stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=True)
    
    # Print stdout line by line as it comes in
    for line in iter(stdout.readline, ""):
        print(line, end="")
    
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"ERROR: Command failed with exit status {exit_status}")
        # Print stderr for debugging
        for line in iter(stderr.readline, ""):
            print(f"[STDERR] {line}", end="")
        raise Exception(f"Command '{command}' failed.")
    print(f"--- Command successful ---")

# --- Main Script Logic ---
try:
    # --- Step 1: Create or find Key Pair ---
    print(f"Checking for key pair: {KEY_NAME}")
    try:
        ec2_client.describe_key_pairs(KeyNames=[KEY_NAME])
        print(f"Key pair '{KEY_NAME}' already exists. Reusing it.")
    except ec2_client.exceptions.ClientError as e:
        if "InvalidKeyPair.NotFound" in str(e):
            print(f"Key pair not found. Creating a new one...")
            key_pair = ec2_client.create_key_pair(KeyName=KEY_NAME)
            with open(KEY_FILE_PATH, 'w') as key_file:
                key_file.write(key_pair['KeyMaterial'])
            if os.name == 'posix': os.chmod(KEY_FILE_PATH, 0o400)
            print(f"Saved private key to '{KEY_FILE_PATH}'")
        else:
            raise e

    # --- Step 2: Launch EC2 Instance (without UserData) ---
    print("Launching a plain EC2 instance...")
    response = ec2_client.run_instances(
        ImageId=AMI_ID,
        MinCount=1,
        MaxCount=1,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[SECURITY_GROUP_ID],
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Jenkins-Flask-Deploy-SSH'}]}]
        # NO UserData HERE - we will configure via SSH
    )
    instance_id = response['Instances'][0]['InstanceId']
    print(f"Instance {instance_id} is launching...")

    # --- Step 3: Wait for Instance to be fully running ---
    ec2_resource = session.resource('ec2')
    instance = ec2_resource.Instance(instance_id)
    instance.wait_until_running()
    instance.reload()
    public_ip = instance.public_ip_address
    print(f"Instance is running at Public IP: {public_ip}")

    # --- Step 4: Wait for SSH to be ready ---
    print("Waiting for SSH service to be available...")
    retries = 10
    for i in range(retries):
        try:
            with socket.create_connection((public_ip, 22), timeout=10):
                print("SSH port 22 is open.")
                break
        except (socket.timeout, ConnectionRefusedError):
            if i < retries - 1:
                print(f"SSH not ready yet. Retrying in 15 seconds... ({i+1}/{retries})")
                time.sleep(15)
            else:
                raise Exception("Could not connect to SSH after multiple retries.")
    
    # --- Step 5: Connect via SSH and run commands ---
    print(f"Connecting to {public_ip} via SSH...")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(KEY_FILE_PATH)
    ssh_client.connect(hostname=public_ip, username='ubuntu', pkey=private_key)
    
    print("SSH connection established. Starting configuration...")
    
    # Combine commands for execution
    full_command_string = " && ".join(REMOTE_COMMANDS)
    execute_remote_command(ssh_client, full_command_string)

    ssh_client.close()
    
    print("\n----------------------------------------------------")
    print("Instance configuration complete!")
    print(f"To SSH: ssh -i {KEY_FILE_PATH} ubuntu@{public_ip}")
    print(f"--> Access your Flask app at: http://{public_ip}:5000")
    print("----------------------------------------------------\n")

except Exception as e:
    print(f"\nAN OVERALL ERROR OCCURRED: {e}")
    sys.exit(1)