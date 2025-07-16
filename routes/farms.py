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
