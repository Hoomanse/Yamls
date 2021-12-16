import logging
import boto3
from botocore.exceptions import ClientError
import os
import config_loader


def upload_file(file_name, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)

    app_config = config_loader.parse_config('../config.yml')
    bucket = app_config.get('aws').get('s3').get('bucket')
    region_name = app_config.get('aws').get('region')
    s3_client = boto3.client('s3',
                             aws_access_key_id=app_config.get('aws').get('access-key'),
                             aws_secret_access_key=app_config.get('aws').get('secret-key'),
                             region_name=region_name)
    try:
        s3_client.upload_file(file_name, bucket, object_name)
        return 'https://' + bucket + '.s3.' + region_name + '.amazonaws.com/' + object_name
    except ClientError as e:
        logging.error(e)
        return False
