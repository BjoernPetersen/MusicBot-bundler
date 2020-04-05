import hashlib
from base64 import b64encode

import boto3


def list_buckets():
    s3 = boto3.resource('s3')
    bucket_names = []
    for bucket in s3.buckets.all():
        bucket_names.append(bucket.name)


def _hash_md5(file) -> bytes:
    md5 = hashlib.md5()
    with open(file, 'rb') as f:
        while chunk := f.read(4096):
            md5.update(chunk)
    bytes = md5.digest()
    return bytes


def store_file(file: str):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('musicbot-bundles')
    md5 = _hash_md5(file)
    base64_md5 = b64encode(md5).decode('ascii')
    hex_md5 = md5.hex()
    key = f'musicbot-desktop-{hex_md5}.zip'
    with open(file, 'rb') as f:
        bucket.put_object(
            Key=key,
            Body=f,
            ContentMD5=base64_md5,
            ContentType='application/zip'
        )
        return {
            'Bucket': 'musicbot-bundles',
            'Key': key,
        }


def get_url(object_id) -> str:
    s3 = boto3.client('s3')
    return s3.generate_presigned_url(
        'get_object',
        Params=object_id,
    )
