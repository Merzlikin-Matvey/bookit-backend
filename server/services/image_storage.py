import io
import os
import uuid

import boto3
from PIL import Image
from botocore.exceptions import ClientError
from fastapi import UploadFile


S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://s3:8003")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")


class ImageStorage:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY
        )
        self.bucket_name = 'images'

        if not self.is_bucket_exists():
            self.create_bucket()

    def is_bucket_exists(self) -> bool:
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False

    def create_bucket(self):
        self.s3.create_bucket(Bucket=self.bucket_name)

    def upload_image(self, image: UploadFile) -> str:
        try:
            image_data = Image.open(image.file)
        except:
            raise ValueError("Unsupported image format")
    
        image_data = Image.open(image.file)
        image_bytes = io.BytesIO()
        image_data.convert("RGB").save(image_bytes, format="JPEG")
        image_bytes.seek(0)

        file_name = str(uuid.uuid4().hex)
        self.s3.upload_fileobj(image_bytes, self.bucket_name, file_name)
        return file_name

    def get_image_url(self, image_name: str) -> str:
        return f"{S3_ENDPOINT_URL}/{self.bucket_name}/{image_name}"

    def get_image(self, image_id: str) -> bytes:
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=image_id)
            return response['Body'].read()
        except ClientError as e:
            print(f"Unable to get image: {e}")

    def upload_default_avatar(self, image: UploadFile) -> str:
        try:
            image_data = Image.open(image.file)
        except Exception:
            raise ValueError("Unsupported image format")
        image_bytes = io.BytesIO()
        image_data.convert("RGB").save(image_bytes, format="JPEG")
        image_bytes.seek(0)
        file_name = "default_avatar"
        self.s3.upload_fileobj(image_bytes, self.bucket_name, file_name)
        return file_name
    
