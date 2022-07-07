###########################################################################
#################0########## AMI IMAGE BUILDER #################0##########
###########################################################################
import logging
import argparse
import boto3
from botocore.exceptions import ClientError
import yaml

############################################################################
### Setupping logger
############################################################################
logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s"
)

############################################################################
### Init AWS resources
############################################################################
def GetImageBuilderClient():
    """
    Getting the image builder client
    """
    imageBuilderClient = boto3.client(
        "imagebuilder",
        region_name=region_name,
        aws_access_key_id=accessKey,
        aws_secret_access_key=secretAccessKey,
    )

    return imageBuilderClient


############################################################################
### Main logic
############################################################################
def CreateComponent(
    componentName, componentSemanticVersion, componentPlatform, component_data
):
    """
    Create a EC2 Image Builder Componet
    """
    try:
        client = GetImageBuilderClient()
        res = client.create_component(
            name=componentName,
            semanticVersion=componentSemanticVersion,
            description="Component created using boto3 API",
            platform=componentPlatform,
            supportedOsVersions=[
                "Ubuntu 18",
            ],
            data=yaml.dump(component_data),
        )
    except ClientError:
        logger.exception("******* Could not create a component")
        raise
    else:
        return res


def CreateImageRecipe(
    recipeName,
    recipeSemanticVersion,
    recipeComponentAmazonResourceName,
    region_name,
    recipeImageName,
    recipeOsVersion,
    accountId,
):
    """
    Create a EC2 Image Builder Recipe
    """
    try:
        client = GetImageBuilderClient()
        recipeImageName = recipeImageName.replace(" ", "-").lower()
        print(
            f"arn:aws:imagebuilder:{region_name}:aws:image/{recipeImageName}/{recipeOsVersion}"
        )
        res = client.create_image_recipe(
            name=recipeName,
            semanticVersion=recipeSemanticVersion,
            components=[
                {
                    "componentArn": f"arn:aws:imagebuilder:{region_name}:{accountId}:component/{recipeComponentAmazonResourceName}/{recipeSemanticVersion}",
                }
            ],
            parentImage=f"arn:aws:imagebuilder:{region_name}:aws:image/{recipeImageName}/{recipeOsVersion}",
        )

    except ClientError:
        logger.exception("******* Could not create image recipe")
        raise
    else:
        return res


def CreateImageDestributionConfiguration(
    destributionName,
    region_name,
):
    """
    Create a EC2 Image Builder Destribution Configuration
    """
    try:
        client = GetImageBuilderClient()
        res = client.create_distribution_configuration(
            name=destributionName,
            distributions=[
                {
                    "region": f"{region_name}",
                    "amiDistributionConfiguration": {
                        "name": "boto-{{imagebuilder:buildDate}}"
                    },
                }
            ],
        )
    except ClientError:
        logger.exception("******* Could not create image destribution configuration")
        raise
    else:
        return res


def CreateImageInfrastructureConfiguration(
    infrastructureName,
    infrastructureType,
    infrastructureInstanceProfileRoleName,
):
    """
    Create a EC2 Image Builder Infrastructure Configuration
    """
    try:
        client = GetImageBuilderClient()
        res = client.create_infrastructure_configuration(
            name=infrastructureName,
            instanceTypes=[f"{infrastructureType}"],
            instanceProfileName=f"{infrastructureInstanceProfileRoleName}",
            terminateInstanceOnFailure=True,
        )
    except ClientError:
        logger.exception("******* Could not create image infrastructure configuration")
        raise
    else:
        return res


def CreateImagePipeline(
    imagePipelineName,
    region_name,
    accountId,
    recipeName,
    recipeSemanticVersion,
    infrastructureName,
    destributionName,
):
    """
    Create a EC2 Image Builder Pipeline
    """
    try:
        client = GetImageBuilderClient()
        recipeName = recipeName.lower()
        infrastructureName = infrastructureName.lower()
        destributionName = destributionName.lower()
        res = client.create_image_pipeline(
            name=imagePipelineName,
            imageRecipeArn=f"arn:aws:imagebuilder:{region_name}:{accountId}:image-recipe/{recipeName}/{recipeSemanticVersion}",
            description="Created using the boto3 API from python",
            infrastructureConfigurationArn=f"arn:aws:imagebuilder:{region_name}:{accountId}:infrastructure-configuration/{infrastructureName}",
            distributionConfigurationArn=f"arn:aws:imagebuilder:{region_name}:{accountId}:distribution-configuration/{destributionName}",
            imageTestsConfiguration={"imageTestsEnabled": True, "timeoutMinutes": 60},
            schedule={
                "scheduleExpression": "cron(0 * * * ?)",
                "timezone": "UTC",
                "pipelineExecutionStartCondition": "EXPRESSION_MATCH_AND_DEPENDENCY_UPDATES_AVAILABLE",
            },
            status="ENABLED",
        )
    except ClientError:
        logger.exception("******* Could not create image pipeline")
        raise
    else:
        return res


###########################################################################
### Parsing arguments
###########################################################################
parser = argparse.ArgumentParser(
    description="Arguments parser for Azure DevOps pipelines"
)
parser.add_argument("-Account_id")
parser.add_argument("-Access_key")
parser.add_argument("-Secret_access_key")
parser.add_argument("-Region_name")
parser.add_argument("-Component_name")
parser.add_argument("-Component_semantic_version")
parser.add_argument("-Component_platform")
parser.add_argument("-Recipe_name")
parser.add_argument("-Recipe_semantic_version")
parser.add_argument("-Recipe_component_amazon_resource_name")
parser.add_argument("-Recipe_image_name")
parser.add_argument("-Recipe_os_version")
parser.add_argument("-Destribution_name")
parser.add_argument("-Infrastructure_name")
parser.add_argument("-Infrastructure_type")
parser.add_argument("-Infrastructure_instance_profile_role_name")
parser.add_argument("-Image_pipeline_name")

args = parser.parse_args()

accountId = args.Account_id
accessKey = args.Access_key
secretAccessKey = args.Secret_access_key
region_name = args.Region_name
componentName = args.Component_name
componentSemanticVersion = args.Component_semantic_version
componentPlatform = args.Component_platform
recipeName = args.Recipe_name
recipeSemanticVersion = args.Recipe_semantic_version
recipeComponentAmazonResourceName = args.Recipe_component_amazon_resource_name
recipeImageName = args.Recipe_image_name
recipeOsVersion = args.Recipe_os_version
destributionName = args.Destribution_name
infrastructureName = args.Infrastructure_name
infrastructureType = args.Infrastructure_type
infrastructureInstanceProfileRoleName = args.Infrastructure_instance_profile_role_name
imagePipelineName = args.Image_pipeline_name

#############################################################################
### Set pathing parameters
#############################################################################
patch = None
lastPatchDate = None

if componentPlatform == "Linux":
    if "Ubuntu" in recipeImageName or "Debian" in recipeImageName:
        payload = "apt update -y"
        lastPatchDate = "cat /var/log/apt/history.log | grep 'End-Date' | tail -1"
    elif "Amazon" in recipeImageName or "Centos" in recipeImageName:
        payload = "yum -y update"
        lastPatchDate = "grep Updated: /var/log/yum.log | tail -1"
    else:
        payload = "echo Patching stage"
        
component_data = {
    "name": "CreateFileAndTestExists",
    "schemaVersion": "1.0",
    "phases": [
        {
            "name": "build",
            "steps": [
                {
                    "name": "Patching",
                    "action": "ExecuteBash",
                    "inputs": {
                        "commands": [
                            "echo Start patching stage...",
                            f"{payload}"
                            ]
                        },
                }
            ],
            "name": "validate",
            "steps": [
                {
                    "name": "Patching",
                    "action": "ExecuteBash",
                    "inputs": {
                        "commands": [
                            "echo Start validation stage...",
                            f"{lastPatchDate}",
                            ]
                        },
                }
            ],
        },
    ],
}

#######################################################################################
### Running funs
#######################################################################################
CreateComponent(
    componentName=componentName,
    componentSemanticVersion=componentSemanticVersion,
    componentPlatform=componentPlatform,
    component_data=component_data,
)
CreateImageRecipe(
    recipeName=recipeName,
    recipeSemanticVersion=recipeSemanticVersion,
    recipeComponentAmazonResourceName=recipeComponentAmazonResourceName,
    region_name=region_name,
    recipeImageName=recipeImageName,
    recipeOsVersion=recipeOsVersion,
    accountId=accountId,
)
CreateImageDestributionConfiguration(
    destributionName=destributionName, region_name=region_name
)
CreateImageInfrastructureConfiguration(
    infrastructureName=infrastructureName,
    infrastructureType=infrastructureType,
    infrastructureInstanceProfileRoleName=infrastructureInstanceProfileRoleName,
)
CreateImagePipeline(
    imagePipelineName=imagePipelineName,
    region_name=region_name,
    accountId=accountId,
    recipeName=recipeName,
    recipeSemanticVersion=recipeSemanticVersion,
    infrastructureName=infrastructureName,
    destributionName=destributionName,
)
