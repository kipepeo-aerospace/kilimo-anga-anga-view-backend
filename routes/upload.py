from fastapi import APIRouter, UploadFile, File, Form, Request
from azure.storage.blob import BlobServiceClient
import os

router = APIRouter()


@router.post("/upload")
async def upload_image(
    request: Request,
    clientId: str = Form(...),
    farmId: str = Form(...),
    farmName: str = Form(...),
    file: UploadFile = File(...)
):
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

    return {"message": "Upload successful", "path": blob_path}
