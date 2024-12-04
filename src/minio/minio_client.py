import os
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error
from fastapi import Request

load_dotenv()

async def create_bucket() -> Minio:
    minio_client = Minio(
        os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ROOT_USER"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
        secure=False
    )

    found = minio_client.bucket_exists(os.getenv("MINIO_BUCKET"))
    if not found:
        minio_client.make_bucket(os.getenv("MINIO_BUCKET"))
        
    return minio_client

def get_minio_client(request: Request):
    return request.app.state.minio_client