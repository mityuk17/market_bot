import os
import boto3
bucket_name = ''
session = boto3.session.Session()

s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id='',
    aws_secret_access_key=''
)


async def load_photo(filepath: str, item_id: int):
    s3.upload_file(filepath, bucket_name, f'{item_id}.png')
    os.remove(filepath)


async def get_link_by_item_id(item_id: int):
    link = f'https://storage.yandexcloud.net/{bucket_name}/{item_id}.png'
    return link
