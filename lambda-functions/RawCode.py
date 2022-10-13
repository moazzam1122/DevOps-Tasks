import json
import botocore
import boto3
import logging
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def insert_msg_in_fifo_sqs_queue(event):
    compute_enviroment_name,job_queue_name,job_definition_name,job_definition_revision = create_aws_batch_job_enviroment()
    print('Input event: {event}'.format(event=event))

    env = os.environ["ENV"].upper()
    
    client_name, project, client_s3_path, client_s3_key, client_s3_bucket = extract_data(event)
    risk_clients_list = ["vibra_risk","humana_risk","hpp_risk","uha_risk","priorityhealth_risk","hpn_risk","dean_mr_risk","ohi_risk","vnsny_risk","mdphycare_risk"]
    multiprojects_list = ["anthem"]
    
    should_proceed = filter_unknown_clients(client_name, project, env)
    aws_batch_job_trigger(compute_enviroment_name,job_queue_name,job_definition_name,job_definition_revision,client_s3_key,client_name,client_s3_bucket)
    
    if not should_proceed and ("risk" not in project.lower() and client_name not in risk_clients_list):
        message = 'Client Name: "{client_name}" and project "{project}" are not recognized. Skipping Client..'.format(client_name=client_name,project=project)
        print(message)
        publish_result(message, "Skipped Client", env)
        return

    data = {"client_name": client_name, "s3_input_path": client_s3_path}
    
    sqs = boto3.client('sqs')
    if client_name.lower() in [i.lower() for i in multiprojects_list] :
        response = sqs.send_message(
            QueueUrl=os.environ["MULTIPROJECT_PROCESSOR_QUEUE_URL"],
            MessageBody=json.dumps(data),
            MessageGroupId='MULTIPROJECT-PROCESSOR-QUEUE-GROUP'
        )
    else:
        response = sqs.send_message(
            QueueUrl=os.environ["PROCESSOR_QUEUE_URL"],
            MessageBody=json.dumps(data),
            MessageGroupId='PROCESSOR-QUEUE-GROUP'
        )        
    
    message = "Message published to etl dag queue.\nsqs message: {data}\nresponse: {response}".format(data=data,response=response)
    print(message)
    publish_result(message, "Success", env)

def extract_data(event):
    
    isSnsEvent = event['Records'][0].get("EventSource") == 'aws:sns'
    if isSnsEvent:
        event = json.loads(event['Records'][0]['Sns']['Message'])
        print('Extracted event: {event}'.format(event=event))
        
    client_s3_bucket = event['Records'][0]['s3']['bucket']['name']
    client_s3_key = event['Records'][0]['s3']['object']['key']
    
    if isSnsEvent:
        client_name = client_s3_bucket.split('-')[3]
    else:
        client_name = client_s3_key.split('/')[0]
        
    project = client_s3_key.split('/')[0]
    client_s3_key = re.search('^.*/',client_s3_key).group()[:-1]
    client_s3_path = 's3://' + client_s3_bucket + '/' + client_s3_key
    
    return client_name, project, client_s3_path, client_s3_key, client_s3_bucket
    
def filter_unknown_clients(client_name, project, env):
    
    file = open('client_project_lkp_{env}.json'.format(env=env))
    client_data = json.load(file)

    if len(client_data) == 0:
        return True
    
    match = next((d for d in client_data if d['client_name'].lower() == client_name.lower()), None)
    if match != None and project.lower() in [i.lower() for i in match['project_name']]:
        return True
        
    return False

def publish_result(message, result, env):
    sns = boto3.client('sns')
    att_dict = {}
    att_dict["resultValue"] = {'DataType': 'String', 'StringValue': result}
    response = sns.publish(
        TopicArn=os.environ["SNS_RESULT_TOPIC"],
        Subject='[{env}] ETL Lambda Result: {result}'.format(env=env,result=result),
        Message=message,
        MessageAttributes=att_dict
    )
    print(response)

def create_aws_batch_job_enviroment():
    compute_enviroment_name = 's3_copy_compute_enviroment'#os.environ["COMPUTE_ENV_NAME"]
    job_queue_name = 's3_copy_queue'#os.environ["BATCH_QUEUE_NAME"]
    region = 'us-east-1'#os.environ["BATCH_JOB_REGION"]
    client = boto3.client('batch',region)
    compute_enviroment_name = create_batch_job_compute_enviroment(compute_enviroment_name,client)
    job_queue_name = create_batch_job_queue(compute_enviroment_name,job_queue_name,client)
    job_definition_name,job_definition_revision = create_batch_job_definition(client)
    return compute_enviroment_name,job_queue_name,job_definition_name,job_definition_revision
             

def create_batch_job_compute_enviroment(compute_enviroment_name,client):    
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

def create_batch_job_queue(compute_enviroment_name,job_queue_name,client):
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

def create_batch_job_definition(client):
    
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
                        {"name": "SOURCE_BUCKET", "value": "test-bucket-source"},
                        {"name": "TARGET_BUCKET", "value": "test-bucket-target"},
                        {"name": "SOURCE_BUKCET_KEY", "value": "test-source/"},
                        {"name": "TARGET_BUKCET_KEY", "value": "test-target/"}
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

def aws_batch_job_trigger(compute_enviroment_name,job_queue_name,job_definition_name,job_definition_revision,client_s3_key,client_name,client_s3_bucket):
    region = 'us-east-1'#os.environ["BATCH_JOB_REGION"]
    client = boto3.client('batch',region)
    dest_s3_bucket_name = os.environ["DESNT_BUCKET"]
    source_path=client_s3_key+'/'
    destination_path=client_name+'/'
    response = client.submit_job(jobName='moazzam-test-batch-job', # use your HutchNet ID instead of 'jdoe'
                                jobQueue=job_queue_name, # sufficient for most jobs
                                jobDefinition=job_definition_name +':'+str(job_definition_revision), # use a real job definition
                                containerOverrides={
                                    "environment": [ # optionally set environment variables
                                        {"name": "SOURCE_BUCKET", "value": client_s3_bucket},
                                        {"name": "TARGET_BUCKET", "value": dest_s3_bucket_name},
                                        {"name": "SOURCE_BUKCET_KEY", "value": source_path},
                                        {"name": "TARGET_BUKCET_KEY", "value": destination_path}
                                    ]
                                })

    logger.info("Job ID is {}.".format(response['jobId'])) 

def lambda_handler(event, context):
    
    insert_msg_in_fifo_sqs_queue(event)
if __name__ == "__main__":
    lambda_handler(None,None)
