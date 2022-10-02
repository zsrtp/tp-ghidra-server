from time import time
import boto3, time

ssm_client = boto3.client('ssm')
ec2_client = boto3.client('ec2')

response = ec2_client.describe_instances(Filters=[
    {
        'Name': 'tag:Name',
                'Values': ['ghidra-*']
    }, {
        'Name': 'instance-state-name',
        'Values': ['running']
    }
])
instance_id = response["Reservations"][0]["Instances"][0]["InstanceId"]

# Run command to list current Ghidra users
run_commands = ["source /etc/profile","/opt/ghidra/server/svrAdmin -list"]
response = ssm_client.send_command(
    InstanceIds=[instance_id],
    DocumentName="AWS-RunShellScript",
    Parameters={'commands': run_commands}, )

# Fetch stdout reponse
command_id = response['Command']['CommandId']
time.sleep(15)
output = ssm_client.get_command_invocation(
    CommandId=command_id,
    InstanceId=instance_id,
)

raw_output = output["StandardOutputContent"]

print(output["StandardOutputContent"])


