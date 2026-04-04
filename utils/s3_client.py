import os
import logging

import aioboto3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "asksimba-images")
S3_REGION = os.getenv("S3_REGION", "garage")

session = aioboto3.Session()


def _get_client():
    return session.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        region_name=S3_REGION,
    )


async def upload_image(file_bytes: bytes, key: str, content_type: str) -> str:
    async with _get_client() as client:
        await client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
    logging.info(f"Uploaded image to S3: {key}")
    return key


async def get_image(key: str) -> tuple[bytes, str]:
    async with _get_client() as client:
        response = await client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        body = await response["Body"].read()
        content_type = response.get("ContentType", "image/jpeg")
    return body, content_type


async def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
    async with _get_client() as client:
        url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
    return url


async def delete_image(key: str) -> None:
    async with _get_client() as client:
        await client.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
    logging.info(f"Deleted image from S3: {key}")
