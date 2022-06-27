import boto3
from botocore.exceptions import ClientError
import logging

########################################################################
## Setupping logger activities
########################################################################
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

########################################################################
## AWS Client Credentials
########################################################################
AWS_ACCESS_KEY_ID='<YOUR-AWS-ACCESS-KEY-ID>'
AWS_SECRET_ACCESS_KEY='YOUR-AWS-SECRET-ACCESS-KEY'
AWS_DEFAULT_REGION='us-east-1'
AWS_AUTH_RESOURCES_CREDENTIALS = boto3.resource(
    'ec2',
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
AWS_AUTH_CLIENT_CREDENTIALS = boto3.client(
    'ec2',
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

########################################################################
## AWS EC2 Configurations
########################################################################
AWS_EC2_IMAGE_ID='ami-08d4ac5b634553e16'
AWS_EC2_INSTANCE_TYPE='t2.micro'
AWS_SSH_KEY_NAMES='ubuntu-ssh'
AWS_EC2_MAX_COUNT=1
AWS_EC2_MIN_COUNT=1
AWS_DRY_RUN_CONFIGURATION=True
AWS_EC2_PRIVATE_IP_ADDRESS='172.31.0.50'
AWS_TAGS_KEY='Name'
AWS_EC2_TAGS_VALUE='Ubuntu 20.04 boto3'

########################################################################
## AWS Security Group Configuration
########################################################################
AWS_SECURITY_GROUP_DESCRIPTION='This is a simple security group'
AWS_SECURITY_GROUP_NAME='sec_devices'
AWS_SECURITY_GROUP_TAGS_VALUE='Securoty group 27.06'

########################################################################
## AWS Network Interface Configuration
########################################################################
AWS_RESOURCE_NETWORK_INTERFACE_DESCRIPTION='This is a simple nic'
AWS_RESOURCE_NETWORK_INTERFACE_PRIVATE_IP_ADDRESS='10.0.0.50'
AWS_RESOURCE_INDEX_DEVICE_NIC=123


########################################################################
## AWS CIDR Block Device Configuration
########################################################################
AWS_RESOURCE_CIDRBLOCK='10.0.0.0/24'

########################################################################
## Main funcs logic
########################################################################
def CreateEC2Instance():
    """
    Create an EC2 instance with Ubuntu OS and SSH keys
    """
    try:
        res = AWS_AUTH_RESOURCES_CREDENTIALS.create_instances(
            ImageId=AWS_EC2_IMAGE_ID,
            InstanceType=AWS_EC2_INSTANCE_TYPE,
            KeyName=AWS_SSH_KEY_NAMES,
            MaxCount=AWS_EC2_MAX_COUNT,
            MinCount=AWS_EC2_MIN_COUNT,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': f'{AWS_TAGS_KEY}',
                            'Value': f'{AWS_EC2_TAGS_VALUE}'
                        }
                    ]  
                },
            ]
        )
    except ClientError:
        logging.exception("******************************** ERROR: Unable to create EC2 instance")
        raise
    else:
        return res 
    
    
def CreateVPC():
    """
    Create a default VPC
    """
    try:
        res = AWS_AUTH_CLIENT_CREDENTIALS.create_default_vpc()
    except ClientError:
        logging.exception("******************************** ERROR: Unable to create a default VPC")
        raise
    else:
        return res 
    

def CreateSecurityGroup():
    """
    Create a security group with the name: sec_devices
    """
    try: 
        AWS_DEFAULT_VPC_ID = GetVPCIds()    
            
        res = AWS_AUTH_RESOURCES_CREDENTIALS.create_security_group(
            Description=AWS_SECURITY_GROUP_DESCRIPTION,
            GroupName=AWS_SECURITY_GROUP_NAME,
            VpcId=AWS_DEFAULT_VPC_ID,
        )
    except ClientError:
        logging.exception("******************************** ERROR: Unable to create a security group")
        raise
    else:
        return res
    

def CreateInternetGateway():
    """
    Create an InternetGateway resource 
    """
    try:
        res = AWS_AUTH_RESOURCES_CREDENTIALS.create_internet_gateway()
    except ClientError:
        logging.exception("******************************** ERROR: Unable to create a internet gateway")
        raise
    else:
        return res


def CreateSubnet():
    """
    Create a subnet
    """
    try:
        AWS_DEFAULT_VPC_ID = GetVPCIds()    
        
        res = AWS_AUTH_RESOURCES_CREDENTIALS.create_subnet(
            VpcId=f'{AWS_DEFAULT_VPC_ID}',
            CidrBlock=f'{AWS_RESOURCE_CIDRBLOCK}'
        )
    except ClientError:
        logging.exception("******************************** ERROR: Unable to create a subnet")
        raise
    else:
        return res 


def CreateNetworkInterface():
    """
    Create a network interface with the IP address: 10.0.0.50
    """
    try:
        AWS_RESOURCE_SECURITY_GROUP_ID = GetSecurityGroupIds()
        AWS_RESOURCE_SUBNET_ID = GetSubnetIds()
        
        res = AWS_AUTH_RESOURCES_CREDENTIALS.create_network_interface(
            Description=AWS_RESOURCE_NETWORK_INTERFACE_DESCRIPTION,
            Groups=[
                f'{AWS_RESOURCE_SECURITY_GROUP_ID}',
            ],
            SubnetId=f'{AWS_RESOURCE_SUBNET_ID}',
        )
    except ClientError:
        logging.exception("******************************** ERROR: Unable to create a network interface")
        raise
    else:
        return res

def CreateRouteTable():
    """
    Create a route table
    """
    try:
        AWS_DEFAULT_VPC_ID = GetVPCIds()
        res = AWS_AUTH_RESOURCES_CREDENTIALS.create_route_table(
            VpcId=f'{AWS_DEFAULT_VPC_ID}',
        )
    except ClientError:
        logging.exception("******************************** ERROR: Unable to create a route table")
        raise
    else:
        return res 
    
########################################################################
## Attaching Resources to each other 
########################################################################
def AttachInternetGatewayToVPC():
    """
    Attaching the InternetGateway to a VPC resource
    """
    try:
        AWS_RESOURCE_INTERNET_GATEWAY_ID = GetInternetGatewayIds()
        AWS_DEFAULT_VPC_ID = GetVPCIds()   
        res = AWS_AUTH_CLIENT_CREDENTIALS.attach_internet_gateway(
            InternetGatewayId=f'{AWS_RESOURCE_INTERNET_GATEWAY_ID}',
            VpcId=f'{AWS_DEFAULT_VPC_ID}',
        ) 
    except ClientError:
        logging.exception("******************************** ERROR: Unable to attach an internet gateway to VPC")
        raise
    else:
        return res 

def AttachNetworkInterfaceToEC2():
    """
    Attaching the Netwire interface to an EC2 instance
    """
    try:
        AWS_RESOURCE_EC2_INSTANCE_ID = GetEC2InstanceIds()
        AWS_RESOURCE_NIC_ID = GetNICIds()
        
        res = AWS_AUTH_CLIENT_CREDENTIALS.attach_network_interface(
            DeviceIndex=AWS_RESOURCE_INDEX_DEVICE_NIC,
            InstanceId=AWS_RESOURCE_EC2_INSTANCE_ID,
            NetworkInterfaceId=AWS_RESOURCE_NIC_ID,
        )
    except ClientError:
        logging.exception("******************************** ERROR: Unable to attach a network interface to EC2 instance")
        raise
    else:
        return res  

########################################################################
## Getting useful ids of resources
########################################################################
def GetVPCIds():
    """
    Getting nessesary ID of the VPC
    """
    vps_ids = AWS_AUTH_CLIENT_CREDENTIALS.describe_vpcs(
            Filters=[{'Name':'isDefault','Values': ['true']},]
        ) 
    return vps_ids['Vpcs'][0]['VpcId']

 
def GetSecurityGroupIds():
    """
    Getting nessesary ID of the security group
    """
    sec_ids = AWS_AUTH_CLIENT_CREDENTIALS.describe_security_groups(
        GroupNames=[f'{AWS_SECURITY_GROUP_NAME}']
    )
    return sec_ids['SecurityGroups'][0]['GroupId']


def GetSubnetIds():
    """
    Getting nessesary ID of the subnet
    """
    subnet_ids = AWS_AUTH_CLIENT_CREDENTIALS.describe_subnets()
    return subnet_ids['Subnets'][0]['SubnetId']

def GetEC2InstanceIds():
    """
    Getting nessesary ID of the ec2 instance
    """
    ec2_ids = AWS_AUTH_CLIENT_CREDENTIALS.describe_instance()
    return ec2_ids['Reservations'][1]['InstanceId']

def GetNICIds():
    """
    Getting nessesary ID of the nics
    """
    nic_ids = AWS_AUTH_CLIENT_CREDENTIALS.describe_network_intertface()
    return nic_ids['NetworkInterfaces'][0]['NetworkInterfaceId']

def GetInternetGatewayIds():
    """
    Getting nessesary ID of the internet gateway interface
    """
    internet_gateway = AWS_AUTH_CLIENT_CREDENTIALS.describe_internet_gateways()
    return internet_gateway['InternetGateways'][0]['InternetGatewayId']
    
    
if __name__ == "__main__":
    """
    Creating nessesary AWS resources 
    """
    logger.info("Creating nessesary AWS resources...")
    CreateEC2Instance()
    CreateVPC()
    CreateInternetGateway()
    CreateSubnet()
    CreateRouteTable()
    CreateSecurityGroup()
    CreateNetworkInterface()
    
    """
    Attaching resources to each other
    """
    logger.info("Attaching nessesary AWS resources...")
    AttachInternetGatewayToVPC()
    AttachNetworkInterfaceToEC2()
    
