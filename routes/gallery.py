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
    farmId: str
    clientId: str
    url: str
    size: float
    type: str
    uploadDate: str


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
    try:
        images_container = request.app.state.images_container
        account_name = request.app.state.account_name
        account_key = request.app.state.account_key

        query = f"""
            SELECT * FROM c 
            WHERE c.clientId = @clientId 
            AND c.farmId = @farmId 
            AND c.type = @fileType
        """

        parameters = [
            {"name": "@clientId", "value": client_id},
            {"name": "@farmId", "value": farm_id},
            {"name": "@fileType", "value": file_type}
        ]

        results = images_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        )

        container_env_map = {
            "raw": request.app.state.raw_images_container,
            "mosaic": request.app.state.mosaic_container,
            "indices": request.app.state.indices_container
        }

        container_name = container_env_map[file_type]

        image_list = []
        for item in results:
            blob_path = f"{container_name}/{client_id}/{farm_id}/{item['filename']}"
            signed_url = generate_signed_url(container_name, account_name, account_key, blob_path)

            image_list.append(ImageFile(
                id=item["id"],
                filename=item["filename"],
                farmId=item["farmId"],
                clientId=item["clientId"],
                url=signed_url,
                size=round(item.get("size", 0) / (1024 * 1024), 2),
                type=item["type"],
                uploadDate=item.get("uploadDate", datetime.utcnow().strftime("%Y-%m-%d"))
            ))

        return image_list

    except Exception as e:
        print("ERROR in /gallery:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
