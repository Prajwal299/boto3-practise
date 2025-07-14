

import boto3

session = boto3.Session(region_name='eu-north-1')  
ec2_console = session.client('ec2')

instance = ec2_console.run_instances(
    ImageId='ami-042b4708b1d05f512',
    MinCount=1,
    MaxCount=1,
    InstanceType='t3.micro',
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'Boto3-deployment'
                }
            ]
        }
    ]
    
)

instance_id = instance['Instances'][0]['InstanceId']
print("Launched instance:", instance_id)
