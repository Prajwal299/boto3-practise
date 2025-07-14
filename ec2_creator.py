

# import boto3

# session = boto3.Session(region_name='eu-north-1')  
# ec2_console = session.client('ec2')

# instance = ec2_console.run_instances(
#     ImageId='ami-042b4708b1d05f512',
#     MinCount=1,
#     MaxCount=1,
#     InstanceType='t3.micro',
#     TagSpecifications=[
#         {
#             'ResourceType': 'instance',
#             'Tags': [
#                 {
#                     'Key': 'Name',
#                     'Value': 'Boto3-deployment-1'
#                 }
#             ]
#         }
#     ],
#     SecurityGroupIds=['sg-0cd0055363c2a2d75'],
#     userData="""
#     #!/bin/bash
#     sudo apt-get update
#     sudo apt-get upgrade -y
#     sudo apt install docker.io -y

#     sudo systemctl start docker
#     sudo systemctl enable docker

#     sudo usermod -aG docker ubuntu
#      """
    
# )

# instance_id = instance['Instances'][0]['InstanceId']
# print("Launched instance:", instance_id)



import boto3
import time

session = boto3.Session(region_name='eu-north-1')
ec2 = session.client('ec2')

# Update with your actual values
AMI_ID = 'ami-042b4708b1d05f512'
INSTANCE_TYPE = 't3.micro'
SECURITY_GROUP_ID = 'sg-0cd0055363c2a2d75'
KEY_NAME = 'your-key-name'  # Required if you want to SSH in manually

# EC2 UserData script
user_data_script = """#!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io git

sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Clone your Flask app project from GitHub
cd /home/ubuntu
git clone https://github.com/Prajwal299/boto3-practise.git

cd boto3-practise/flask-app-3

# Build Docker image
sudo docker build -t flask-app-3 .

# Run container
sudo docker run -d -p 5000:5000 --name flask-app-3 flask-app-3
"""

# Launch EC2 instance
response = ec2.run_instances(
    ImageId=AMI_ID,
    MinCount=1,
    MaxCount=1,
    InstanceType=INSTANCE_TYPE,
    KeyName=KEY_NAME,
    SecurityGroupIds=[SECURITY_GROUP_ID],
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'Boto3-deployment-1'}]
        }
    ],
    UserData=user_data_script
)

instance_id = response['Instances'][0]['InstanceId']
print("Launched instance:", instance_id)

# Wait until the instance is running
ec2_resource = session.resource('ec2')
instance = ec2_resource.Instance(instance_id)

print("Waiting for instance to be in 'running' state...")
instance.wait_until_running()

# Refresh instance data
instance.load()
print("Public IP:", instance.public_ip_address)
