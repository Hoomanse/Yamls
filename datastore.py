import base64
import boto3
import os
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])


def lambda_handler(event, context):
    with table.batch_writer() as batch:

        for record in event['Records']:
            payload= base64.b64decode(record["kinsesis"]["data"])

            batch.put_item(
                Item=json.loads(payload)
            )