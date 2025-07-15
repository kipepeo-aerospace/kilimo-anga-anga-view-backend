from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

router = APIRouter()

class Farm(BaseModel):
    id: str
    clientId: str
    name: str
    createdAt: str
    imageCount: int

@router.get("/users/{user_id}/farms", response_model=List[Farm])
def get_user_farms(user_id: str, request: Request):
    blob_service = request.app.state.blob_client
    container_name = request.app.state.raw_images_container  # Only count from raw container
    container_client = blob_service.get_container_client(container_name)

    prefix = f"{container_name}/{user_id}/"
    seen_farms: Dict[str, int] = {}

    try:
        blobs = container_client.list_blobs(name_starts_with=prefix)

        for blob in blobs:
            parts = blob.name.split("/")
            if len(parts) < 3:
                continue

            _, client_id, farm_id = parts[:3]
            if farm_id not in seen_farms:
                seen_farms[farm_id] = 0
            seen_farms[farm_id] += 1

        farms = [
            Farm(
                id=farm_id,
                clientId=user_id,
                name=f"Farm {farm_id[-3:].upper()}",  # fallback name
                createdAt="",  # You can fill this later if needed
                imageCount=image_count
            )
            for farm_id, image_count in seen_farms.items()
        ]
        return farms

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
