import boto3
import logging
from typing import Any
from botocore.config import Config
from botocore.exceptions import ClientError
from src.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        endpoint_url = settings.AWS_S3_ENDPOINT_URL
        if endpoint_url and not endpoint_url.startswith(("http://", "https://")):
            endpoint_url = f"https://{endpoint_url}"

        self.endpoint_url = endpoint_url
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=self.endpoint_url if self.endpoint_url else None,
            config=Config(
                max_pool_connections=20,
                retries={"max_attempts": 2},
                read_timeout=10,
                connect_timeout=3,
            ),
        )
        self.bucket_name = settings.S3_BUCKET

    def upload_file(self, file_path: str, object_name: str, content_type: str = None) -> str:
        """
        Uploads a file to an S3 bucket and returns the public/private URL.
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3_client.upload_file(file_path, self.bucket_name, object_name, ExtraArgs=extra_args)

            if self.endpoint_url:
                endpoint = self.endpoint_url.rstrip("/")
                url = f"{endpoint}/{self.bucket_name}/{object_name}"
            else:
                url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
            return url
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return ""

    def get_file_stream(self, object_name: str) -> Any:
        """
        Gets a file stream for an object in S3.
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_name)
            return response
        except ClientError as e:
            logger.error(f"S3 fetch failed: {e}")
            raise

    def generate_presigned_url(self, object_name: str, expires_in: int = 300) -> str:
        """
        Generates a presigned URL for a specific object.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            return ""

    def delete_all_objects(self) -> int:
        """
        Deletes all objects in the bucket. Returns the count of deleted objects.
        """
        try:
            count = 0
            paginator = self.s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket_name):
                if "Contents" in page:
                    delete_keys = {"Objects": [{"Key": obj["Key"]} for obj in page["Contents"]]}
                    response = self.s3_client.delete_objects(Bucket=self.bucket_name, Delete=delete_keys)
                    count += len(response.get("Deleted", []))
            return count
        except ClientError as e:
            logger.error(f"S3 deletion failed: {e}")
            raise

s3_service = S3Service()