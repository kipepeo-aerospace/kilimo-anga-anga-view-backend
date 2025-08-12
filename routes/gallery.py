from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel
from typing import List
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from datetime import datetime, timedelta
import os
import traceback
from helpers.image_conversion import convert_tif_to_jpg_and_upload

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
        account_name = request.app.state.account_name
        account_key = request.app.state.account_key
        
        # Map container name based on file type
        container_env_map = {
            "raw": request.app.state.raw_images_container,
            "mosaic": request.app.state.mosaic_container,
            "indices": request.app.state.indices_container
        }

        container_name = container_env_map[file_type]

        if not container_name:
            raise HTTPException(status_code=404, detail="Container not found for the specified file type.")

        
        # Get the list of blobs the images container
        blob_service_client = request.app.state.blob_client # get the blob service client from app state
        images_container = blob_service_client.get_container_client(container_name)
        
        blobs = images_container.list_blobs(name_starts_with=f"{container_name}/{client_id}/{farm_id}/") 
        results = list(blobs)
        
        # Generate signed URLs for each image
        image_list = []
        
        for item in results:
            filename = item.name.split('/')[-1]

            print(f"[DEBUG] Getting image: {filename} an image of type: {file_type} for farm: {farm_id}")
            
            # Check if the file is a TIF and convert it to JPG for viewing
            if filename.lower().endswith(".tif"):
                # Build the expected JPG filename
                jpg_filename = filename[:-4] + ".jpg"  # replace .tif with .jpg
                jpg_blob_path = f"{container_name}/{client_id}/{farm_id}/{jpg_filename}"

                jpg_blob_client = images_container.get_blob_client(jpg_blob_path)

                # Check if JPG already exists
                try:
                    # Check if JPG exists
                    jpg_blob_client.get_blob_properties()
                    # JPG exists, so use it and skip conversion
                    continue
                except Exception:
                    # JPG does not exist, convert and upload
                    continue

            blob_path = f"{container_name}/{client_id}/{farm_id}/{filename}"
            signed_url = generate_signed_url(container_name, account_name, account_key, blob_path)
             
            image_list.append(ImageFile(
                id=file_type,
                filename=filename,
                farmId=farm_id,
                clientId=client_id,
                url=signed_url,
                size=round(item.get("size", 0) / (1024 * 1024), 2),
                type=file_type,
                uploadDate=item.get("uploadDate", datetime.utcnow().strftime("%Y-%m-%d"))
            ))

        return image_list

    except Exception as e:
        print("ERROR in /gallery:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
