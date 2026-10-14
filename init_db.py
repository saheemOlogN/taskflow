"""Idempotent table creation. Defaults to AWS; Compose supplies a local endpoint."""
import os
import boto3
from botocore.exceptions import ClientError


def initialize():
    db = boto3.resource('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-south-1'),
                        endpoint_url=os.getenv('DYNAMODB_ENDPOINT_URL') or None)
    name = os.getenv('TABLE_NAME', 'devops-tasks')
    try:
        table = db.create_table(TableName=name, KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                                AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                                BillingMode='PAY_PER_REQUEST')
    except ClientError as error:
        if error.response['Error']['Code'] != 'ResourceInUseException':
            raise
        table = db.Table(name)
    table.wait_until_exists()
    print(f'Table ready: {name}')


if __name__ == '__main__':
    initialize()
