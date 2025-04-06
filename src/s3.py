import os
import boto3

from botocore.client import Config


S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

s3 = boto3.client('s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id='YCAJEn5WrL89R1CQT-JETGh3p',  # Service-user recepter-s3 with the role 'storage.objectAdmin'
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version='s3v4'))
bucket_name = 'recepter'


def upload_file(file_name, bucket, object_name):
    try:
        s3.upload_file(file_name, bucket, object_name)
        return True
    except Exception as e:
        print(f"Failed to upload {file_name} to s3")
        print(e)
        return False
