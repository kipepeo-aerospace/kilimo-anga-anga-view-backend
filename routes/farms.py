from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from azure.cosmos.exceptions import CosmosResourceNotFoundError

router = APIRouter()

class Farm(BaseModel):
    id: str
    clientId: str
    name: str
    createdAt: str
    imageCount: int

@router.get("/users/{user_id}/farms", response_model=List[Farm])
def get_user_farms(user_id: str, request: Request):
    farms_container = request.app.state.farms_container

    try:
        query = f"SELECT * FROM c WHERE c.clientId = @userId"
        farms = list(farms_container.query_items(
            query=query,
            parameters=[{"name": "@userId", "value": user_id}],
            enable_cross_partition_query=True
        ))

        return farms

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/farms/{farm_id}", response_model=Farm)
def get_farm_details(user_id: str, farm_id: str, request: Request):
    farms_container = request.app.state.farms_container

    try:
        query = """
        SELECT * FROM c 
        WHERE c.clientId = @userId AND c.id = @farmId
        """
        items = list(farms_container.query_items(
            query=query,
            parameters=[
                {"name": "@userId", "value": user_id},
                {"name": "@farmId", "value": farm_id}
            ],
            enable_cross_partition_query=True
        ))

        if not items:
            raise HTTPException(status_code=404, detail="Farm not found")

        return items[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
