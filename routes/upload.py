from fastapi import APIRouter, UploadFile, File, Form, Request
from azure.storage.blob import BlobServiceClient
import os
from pydantic import BaseModel
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from datetime import datetime
import uuid

router = APIRouter()

class Farm(BaseModel):
    id: str
    clientId: str
    name: str
    createdAt: str
    imageCount: int

class ImageFile(BaseModel):
    id: str
    filename: str
    farmId: str
    clientId: str
    url: str
    size: float
    type: str
    uploadDate: str

@router.post("/upload")
async def upload_image(
    request: Request,
    clientId: str = Form(...),
    farmId: str = Form(...),
    farmName: str = Form(...),
    file: UploadFile = File(...)
):
    
    # start the blob client
    blob_service_client = request.app.state.blob_client # get the blob service client from app state
    container_name = request.app.state.raw_images_container  # get the container name from app state

    if not blob_service_client:
        return {"error": "Blob service client is not initialized."}

    if not container_name:
        return {"error": "Container name is not set."}

    # Log the upload details
    print(f"[UPLOAD] Client: {clientId}, Farm: {farmId}, File: {file.filename}")
    blob_path = f"{container_name}/{clientId}/{farmId}/{file.filename}"
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)

    contents = await file.read()
    blob_client.upload_blob(contents, overwrite=True)

    # Get blob size after upload
    properties = blob_client.get_blob_properties()
    size = properties.size # image size
    upload_date = properties.last_modified.strftime("%Y-%m-%d") # image_upload

    #first check to see if farm exists, if not create a new instance in db
    farms_container = request.app.state.farms_container
    try:
        farm_doc = farms_container.read_item(item=farmId, partition_key=clientId)
        farm_doc["imageCount"] = farm_doc.get("imageCount", 0) + 1
        farms_container.replace_item(item=farmId, body=farm_doc)
    except CosmosResourceNotFoundError:
        # If not found, create farm document
        farm = {
            "id": farmId,
            "clientId": clientId,
            "name": farmName,
            "imageCount": 1,
            "createdAt": datetime.utcnow().isoformat()
        }
        farms_container.create_item(body=farm)

    
    # first check to see if image metadata exists, if not create a new instance in db
    images_container = request.app.state.images_container
    
    # Check if image with same filename already exists
    query = """
        SELECT * FROM c 
        WHERE c.filename = @filename AND c.clientId = @clientId AND c.farmId = @farmId
    """
    parameters = [
        {"name": "@filename", "value": file.filename},
        {"name": "@clientId", "value": clientId},
        {"name": "@farmId", "value": farmId}
    ]
    existing = list(images_container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))

    if not existing:
        imageId = str(uuid.uuid4())
        image = {
            "id": imageId,
            "filename": file.filename,
            "clientId": clientId,
            "farmId": farmId,
            "type": "raw",
            "size": size,
            "uploadDate": upload_date
        }
        images_container.create_item(body=image)

    
    return {"message": "Upload successful", "path": blob_path}
