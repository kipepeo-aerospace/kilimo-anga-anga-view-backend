from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel
from typing import List
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import os
import traceback

router = APIRouter()

class ImageFile(BaseModel):
    id: str
    filename: str
    url: str
    size: int
    type: str

def generate_signed_url(container_name, account_name, account_key, blob_name):
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    return f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

@router.get("/users/{client_id}/gallery", response_model=List[ImageFile])
def list_user_images(
    client_id: str,
    farm_id: str = Query(...),
    file_type: str = Query(..., regex="^(raw|mosaic|indices)$"),
    request: Request = None
):
    container_env_map = {
        "raw": request.app.state.raw_images_container,
        "mosaic": request.app.state.mosaic_container,
        "indices": request.app.state.indices_container
    }

    container_name = container_env_map.get(file_type)

    if not container_name:
        raise HTTPException(status_code=500, detail="Missing container name in env")

    blob_service = request.app.state.blob_client
    container_client = blob_service.get_container_client(container_name)

    prefix = f"{container_name}/{client_id}/{farm_id}/"

    try:
        blobs = container_client.list_blobs(name_starts_with=prefix)
        account_name = request.app.state.account_name
        account_key = request.app.state.account_key
        image_list = []

        for blob in blobs:
            signed_url = generate_signed_url(container_name, account_name, account_key, blob.name)
            image_list.append(ImageFile(
                id=blob.name.split("/")[-1],
                filename=blob.name.split("/")[-1],
                url=signed_url,
                size=blob.size,
                type=file_type
            ))
        return image_list

    except Exception as e:
        print("ERROR in /gallery:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
