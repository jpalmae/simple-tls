import os
import uuid
from minio import Minio
from minio.error import S3Error
from werkzeug.utils import secure_filename
from flask import current_app

class MinioService:
    def __init__(self, app=None):
        self.client = None
        self.bucket = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        endpoint = app.config.get('MINIO_ENDPOINT', 'localhost:9000')
        access_key = app.config.get('MINIO_ACCESS_KEY', 'minio_admin')
        secret_key = app.config.get('MINIO_SECRET_KEY', 'minio_password')
        self.bucket = app.config.get('MINIO_BUCKET', 'lms-assets')
        
        # Remove http:// or https:// from endpoint for minio client
        if endpoint.startswith('http://'):
            endpoint = endpoint[7:]
        elif endpoint.startswith('https://'):
            endpoint = endpoint[8:]

        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False # True si usaras HTTPS directamente a MinIO
        )
        
        # Ensure bucket exists
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)

            # Set bucket policy to public read so browsers can load assets directly
            import json
            policy = json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket}/*"]
                }]
            })
            self.client.set_bucket_policy(self.bucket, policy)
        except S3Error as err:
            print(f"Error checking/creating MinIO bucket: {err}")

    def upload_file(self, file_stream, original_filename, folder_path, content_type=None):
        """
        Uploads a file to MinIO with a UUID to prevent collisions.
        Returns the object name (path in MinIO).
        """
        if not file_stream or not original_filename:
            return None
            
        ext = os.path.splitext(original_filename)[1]
        safe_name = f"{uuid.uuid4().hex}{ext}"
        object_name = f"{folder_path}/{safe_name}"
        
        # Move file pointer to end to get size, then reset
        file_stream.seek(0, os.SEEK_END)
        size = file_stream.tell()
        file_stream.seek(0)
        
        if not content_type:
            content_type = "application/octet-stream"
            
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=file_stream,
                length=size,
                content_type=content_type
            )
            return object_name
        except S3Error as err:
            current_app.logger.error(f"Error uploading to MinIO: {err}")
            return None

    def get_file_url(self, object_name):
        """Returns a public URL accessible from the browser."""
        if not object_name:
            return None
        try:
            # Use public endpoint (browser-reachable) instead of internal Docker hostname
            public_endpoint = current_app.config.get('MINIO_PUBLIC_ENDPOINT')
            if not public_endpoint:
                # Fallback: try to build from internal endpoint replacing docker hostname
                public_endpoint = current_app.config.get('MINIO_ENDPOINT', 'localhost:9000')
            
            bucket = current_app.config.get('MINIO_BUCKET', 'lms-assets')
            if not public_endpoint.startswith('http'):
                public_endpoint = f"http://{public_endpoint}"
                
            return f"{public_endpoint}/{bucket}/{object_name}"
        except Exception as err:
            current_app.logger.error(f"Error getting URL from MinIO: {err}")
            return None

    def delete_file(self, object_name):
        """Deletes a file from MinIO"""
        if not object_name:
            return False
            
        try:
            self.client.remove_object(self.bucket, object_name)
            return True
        except S3Error as err:
            current_app.logger.error(f"Error deleting from MinIO: {err}")
            return False
