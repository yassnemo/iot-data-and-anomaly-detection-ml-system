"""
Common utilities shared across modules
"""
import os
from typing import Optional
from minio import Minio
from minio.error import S3Error


def get_minio_client() -> Minio:
    """Get MinIO client instance"""
    endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    
    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )


def ensure_bucket_exists(bucket_name: str):
    """Ensure MinIO bucket exists"""
    client = get_minio_client()
    
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Created bucket: {bucket_name}")
        else:
            print(f"Bucket exists: {bucket_name}")
    except S3Error as e:
        print(f"Error creating bucket: {e}")
        raise


def upload_to_minio(bucket_name: str, object_name: str, file_path: str):
    """Upload file to MinIO"""
    client = get_minio_client()
    
    try:
        client.fput_object(bucket_name, object_name, file_path)
        print(f"Uploaded {file_path} to {bucket_name}/{object_name}")
    except S3Error as e:
        print(f"Error uploading to MinIO: {e}")
        raise


def download_from_minio(bucket_name: str, object_name: str, file_path: str):
    """Download file from MinIO"""
    client = get_minio_client()
    
    try:
        client.fget_object(bucket_name, object_name, file_path)
        print(f"Downloaded {bucket_name}/{object_name} to {file_path}")
    except S3Error as e:
        print(f"Error downloading from MinIO: {e}")
        raise
