import os
import tempfile
from PIL import Image
from azure.storage.blob import BlobServiceClient

def convert_tif_to_jpg_and_upload(blob_service_client: BlobServiceClient, container_name: str, blob_name: str) -> str:
    """
    Downloads a TIF from Azure Blob Storage, converts it to JPG,
    uploads the JPG back, and returns the JPG blob name.
    """

    print(f"[DEBUG] Starting TIF → JPG conversion for blob: {blob_name} in container: {container_name}")
    # Get blob client for the original tif
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    # Download TIF to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp_tif:
        download_stream = blob_client.download_blob()
        tmp_tif.write(download_stream.readall())
        tif_path = tmp_tif.name

    # Convert TIF to JPG
    jpg_path = tif_path.replace(".tif", ".jpg")
    with Image.open(tif_path) as img:
        img = img.convert("RGB")
        img.save(jpg_path, "JPEG", quality=90)

    # Define JPG blob name (same path, .jpg extension)
    jpg_blob_name = os.path.splitext(blob_name)[0] + ".jpg"

    # Upload JPG to the same container
    jpg_blob_client = blob_service_client.get_blob_client(container=container_name, blob=jpg_blob_name)
    with open(jpg_path, "rb") as jpg_file:
        jpg_blob_client.upload_blob(jpg_file, overwrite=True)

    # Cleanup temp files
    os.remove(tif_path)
    os.remove(jpg_path)

    return jpg_blob_name
