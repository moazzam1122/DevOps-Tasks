import botocore
import boto3
import logging
import json
import re
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
region = 'us-east-1'#os.environ["BATCH_JOB_REGION"]
client = boto3.client('batch',region)

def create_aws_batch_job_enviroment():
    compute_enviroment_name = 's3_copy_compute_enviroment'
    job_queue_name = 's3_copy_queue'
    compute_enviroment_name = create_batch_job_compute_enviroment(compute_enviroment_name)
    # if compute_enviroment_name is None:
    #     return False
    # else:     
    job_queue_name = create_batch_job_queue(compute_enviroment_name,job_queue_name)
        # if job_queue_name is None:
        #     return False
        # else:
    job_definition_name,job_definition_revision = create_batch_job_definition(compute_enviroment_name,job_queue_name)
            
            # if job_definition_name is None:
            #     return False
            # else:
    return compute_enviroment_name,job_queue_name,job_definition_name,job_definition_revision
             

def create_batch_job_compute_enviroment(compute_enviroment_name):    
    try:
        logger.info('Creating AWS Batch Job Compute Enviroment')
        response = client.create_compute_environment(
            computeEnvironmentName = compute_enviroment_name,
            type ='MANAGED',
            state ='ENABLED',
            computeResources = {
                'type': 'FARGATE',
                'maxvCpus': 256,
                'subnets': [
                    'subnet-0360d01cc4438e6ae',
                    'subnet-0ac58760a8c029250',
                    'subnet-097a792aa45b104ad',
                ],
                'securityGroupIds': [
                    'sg-09956750bf9a95405',
                ]
            }
        )
        compute_enviroment_name = response['computeEnvironmentName']
        logger.info('Compute Enviroment Name : {}'.format(compute_enviroment_name))
        print(response)
        return compute_enviroment_name
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Message'] == 'Object already exists':
            logger.info('Compute Enviroment Already Exist')
            return compute_enviroment_name    
        else:
            raise error

def create_batch_job_queue(compute_enviroment_name,job_queue_name):
    try:
        logger.info('Creating AWS Batch Job Queue')
        response = client.create_job_queue(
            jobQueueName=job_queue_name,
            state='ENABLED',
            priority=1,
            computeEnvironmentOrder=[
                {
                    'order': 1,
                    'computeEnvironment': compute_enviroment_name
                },
            ],
        )
        print(response)
        job_queue_name = response['jobQueueName']
        logger.info('job Queue Name : {}'.format(job_queue_name))
        return job_queue_name
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Message'] == 'Object already exists':
            logger.info('Compute Enviroment Already Exist')
            return job_queue_name
        raise error

def create_batch_job_definition(compute_enviroment_name,job_queue_name):
    
    try:
        logger.info('Creating AWS Batch Job Definition')    
        response = client.register_job_definition(
            jobDefinitionName='s3_copy_job_definition',
            type='container',
            containerProperties={
                'image': 'public.ecr.aws/y2a9o9h4/s3_copy:latest',#os.environ["ECR_S3_COPY_IMAGE_URI"]
                'jobRoleArn': 'arn:aws:iam::test:role/ecsTaskExecutionRole', #os.environ["BATCH_JOB_ROLE_ARN"]
                'executionRoleArn': 'arn:aws:iam::test:role/ecsTaskExecutionRole', #os.environ["BATCH_JOB_ROLE_ARN"]
                'environment': [
                        {"name": "SOURCE_BUCKET", "value": "moazzam-test-bucket-source"},
                        {"name": "TARGET_BUCKET", "value": "moazzmtesttarget"},
                        {"name": "SOURCE_BUKCET_KEY", "value": "images/"},
                        {"name": "TARGET_BUKCET_KEY", "value": "four/"}
                ],
                'resourceRequirements': [
                    {
                        'value': '2048',
                        'type': 'MEMORY'
                    },
                    {
                        'value': '1',
                        'type': 'VCPU'
                    }
                ],
                'networkConfiguration': {
                    'assignPublicIp': 'ENABLED'
                },
                'fargatePlatformConfiguration': {
                    'platformVersion': '1.4.0'
                }
            },
            platformCapabilities= ['FARGATE']
        )

        job_definition_name = response['jobDefinitionName']
        job_definition_revision = response['revision']
        logger.info('job Definition Name : {}'.format(job_definition_name))
        return job_definition_name,job_definition_revision
    except botocore.exceptions.ClientError as error:
        raise error
def aws_batch_job_trigger(job_queue_name,job_definition_name,job_definition_revision):

    response = client.submit_job(jobName='moazzam-test-batch-job', # use your HutchNet ID instead of 'jdoe'
                                jobQueue=job_queue_name, # sufficient for most jobs
                                jobDefinition=job_definition_name +':'+str(job_definition_revision), # use a real job definition
                                containerOverrides={
                                    "environment": [ # optionally set environment variables
                                        {"name": "SOURCE_BUCKET", "value": "moazzam-test-bucket-source"},
                                        {"name": "TARGET_BUCKET", "value": "moazzmtesttarget"},
                                        {"name": "SOURCE_BUKCET_KEY", "value": "images/"},
                                        {"name": "TARGET_BUKCET_KEY", "value": "four/"}
                                    ]
                                })

    print("Job ID is {}.".format(response['jobId']))   
def lambda_handler (event, context):
    compute_enviroment_name,job_queue_name,job_definition_name,job_definition_revision = create_aws_batch_job_enviroment()
    print(compute_enviroment_name,job_queue_name,job_definition_name,job_definition_revision)
    aws_batch_job_trigger(job_queue_name,job_definition_name,job_definition_revision)

