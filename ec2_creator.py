# ec2_creator.py

import boto3
import os
import sys
import time
import paramiko
import socket

# --- CONFIGURATION ---
AWS_REGION = 'eu-north-1'
AMI_ID = 'ami-042b4708b1d05f512'
INSTANCE_TYPE = 't3.micro'
SECURITY_GROUP_ID = 'sg-0cd0055363c2a2d75'

KEY_NAME = 'jenkins-boto3-persistent-key'
KEY_FILE_PATH = f'{KEY_NAME}.pem'
GIT_REPO_URL = 'https://github.com/Prajwal299/boto3-practise.git'

# --- REMOTE COMMANDS (MODIFIED FOR AUTOMATION & GRANULAR EXECUTION) ---
REMOTE_COMMANDS = [
    "echo '--- Updating package lists ---'",
    "sudo DEBIAN_FRONTEND=noninteractive apt-get update -yq",
    "echo '--- Installing Docker and Git ---'",
    "sudo DEBIAN_FRONTEND=noninteractive apt-get install -yq docker.io git",
    "echo '--- Starting and enabling Docker ---'",
    "sudo systemctl start docker",
    "sudo systemctl enable docker",
    "echo '--- Adding ubuntu user to docker group ---'",
    "sudo usermod -aG docker ubuntu",
    "echo '--- Cloning application repository ---'",
    f"git clone {GIT_REPO_URL} /home/ubuntu/boto3-practise",
    "echo '--- Building Docker image ---'",
    "sudo docker build -t flask-app-3 /home/ubuntu/boto3-practise/flask-app-3",
    "echo '--- Running Docker container ---'",
    "sudo docker run -d -p 5000:5000 --name my-flask-container flask-app-3"
]

print("--- Starting EC2 Instance Deployment ---")

session = boto3.Session(region_name=AWS_REGION)
ec2_client = session.client('ec2')

# --- Helper function to execute commands remotely ---
def execute_remote_command(ssh_client, command):
    print(f"\n>>> EXECUTING: {command}")
    channel = ssh_client.get_transport().open_session()
    channel.get_pty()
    channel.exec_command(command)
    
    while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
        if channel.recv_ready():
            # THE FIX: Write raw bytes directly to the buffer, bypassing Python's print() encoding.
            sys.stdout.buffer.write(channel.recv(1024))
            sys.stdout.flush()
        if channel.recv_stderr_ready():
            sys.stderr.buffer.write(channel.recv_stderr(1024))
            sys.stderr.flush()

    exit_status = channel.recv_exit_status()
    if exit_status != 0:
        print(f"\nERROR: Command failed with exit status {exit_status}.")
        raise Exception(f"Remote command execution failed.")
    print(f"\n>>> SUCCESS: Command finished.")

# --- Main Script Logic ---
try:
    # Step 1: Ensure Security Group rules exist
    print(f"Ensuring inbound rules on Security Group '{SECURITY_GROUP_ID}'...")
    try:
        ec2_client.authorize_security_group_ingress(GroupId=SECURITY_GROUP_ID, IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}])
        print("Successfully added inbound rule for SSH (port 22).")
    except ec2_client.exceptions.ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e): print("Inbound rule for SSH (port 22) already exists.")
        else: raise e
    try:
        ec2_client.authorize_security_group_ingress(GroupId=SECURITY_GROUP_ID, IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 5000, 'ToPort': 5000, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}])
        print("Successfully added inbound rule for Flask App (port 5000).")
    except ec2_client.exceptions.ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e): print("Inbound rule for Flask App (port 5000) already exists.")
        else: raise e

    # Step 2: Create or find Key Pair
    print(f"\nChecking for key pair: {KEY_NAME}")
    try:
        ec2_client.describe_key_pairs(KeyNames=[KEY_NAME])
        print(f"Key pair '{KEY_NAME}' already exists.")
    except ec2_client.exceptions.ClientError as e:
        if "InvalidKeyPair.NotFound" in str(e):
            print(f"Key pair not found. Creating a new one...")
            key_pair = ec2_client.create_key_pair(KeyName=KEY_NAME)
            with open(KEY_FILE_PATH, 'w') as key_file: key_file.write(key_pair['KeyMaterial'])
            if os.name == 'posix': os.chmod(KEY_FILE_PATH, 0o400)
            print(f"Saved private key to '{KEY_FILE_PATH}'")
        else: raise e

    # Step 3: Launch EC2 Instance
    print("\nLaunching a plain EC2 instance...")
    response = ec2_client.run_instances(ImageId=AMI_ID, MinCount=1, MaxCount=1, InstanceType=INSTANCE_TYPE, KeyName=KEY_NAME, SecurityGroupIds=[SECURITY_GROUP_ID], TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Jenkins-Flask-Deploy-SSH-14'}]}])
    instance_id = response['Instances'][0]['InstanceId']
    print(f"Instance {instance_id} is launching...")

    # Step 4: Wait for Instance and SSH
    ec2_resource = session.resource('ec2')
    instance = ec2_resource.Instance(instance_id)
    instance.wait_until_running()
    instance.reload()
    public_ip = instance.public_ip_address
    print(f"Instance is running at Public IP: {public_ip}")

    print("Waiting for SSH service to be available...")
    for i in range(12):
        try:
            with socket.create_connection((public_ip, 22), timeout=10):
                print("SSH port 22 is open. Connection successful.")
                time.sleep(5)
                break
        except (socket.timeout, ConnectionRefusedError, OSError):
            if i < 11:
                print(f"SSH not ready yet. Retrying in 15 seconds... ({i+1}/12)")
                time.sleep(15)
            else: raise Exception("Could not connect to SSH after multiple retries.")
    
    # Step 5: Connect via SSH and run commands
    print(f"\nConnecting to {public_ip} via SSH...")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(KEY_FILE_PATH)
    ssh_client.connect(hostname=public_ip, username='ubuntu', pkey=private_key)
    
    print("SSH connection established. Starting configuration...")
    # Execute each command individually
    for command in REMOTE_COMMANDS:
        execute_remote_command(ssh_client, command)
    ssh_client.close()
    
    print("\n----------------------------------------------------")
    print("SUCCESS: Instance configuration complete!")
    print(f"To SSH into the instance: ssh -i {KEY_FILE_PATH} ubuntu@{public_ip}")
    print(f"--> Access your Flask app at: http://{public_ip}:5000")
    print("----------------------------------------------------\n")

except Exception as e:
    print(f"\nAN OVERALL ERROR OCCURRED: {e}")
    sys.exit(1)