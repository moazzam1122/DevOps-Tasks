import boto3

batch = boto3.client('batch','us-east-1')

response = batch.submit_job(jobName='moazzam-test-batch-job', # use your HutchNet ID instead of 'jdoe'
                            jobQueue='s3_copy', # sufficient for most jobs
                            jobDefinition='S3_COPY:8', # use a real job definition
                            containerOverrides={
                                "environment": [ # optionally set environment variables
                                    {"name": "SOURCE_BUCKET", "value": "moazzam-test-bucket-source"},
                                    {"name": "TARGET_BUCKET", "value": "moazzmtesttarget"},
                                    {"name": "SOURCE_BUKCET_KEY", "value": "images/source/"},
                                    {"name": "TARGET_BUKCET_KEY", "value": "one/"}
                                ]
                            })

print("Job ID is {}.".format(response['jobId']))