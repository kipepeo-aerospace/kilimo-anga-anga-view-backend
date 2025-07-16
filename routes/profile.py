from fastapi import APIRouter, Path, Request, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from azure.cosmos.exceptions import CosmosResourceNotFoundError

router = APIRouter()

class UserProfile(BaseModel):
    clientId: str
    email: str
    farmsCount: int
    imagesCount: int
    totalProcessingJobs: int
    signupDate: datetime

class User(BaseModel):
    clientId: str
    email: str
    displayName: str
    signupDate: datetime

@router.get("/users/{user_id}/profile", response_model=UserProfile)
def get_user_profile(
    request: Request,
    user_id: str = Path(..., description="The user's unique id name from Entra"),
    email: str = Query(...),
    displayName: str = Query(...)
    ):
    
    # Call the database containers
    users_container = request.app.state.users_container
    farms_container = request.app.state.farms_container
    images_container = request.app.state.images_container
    jobs_container = request.app.state.jobs_container
    
    #first check to see if user exists
    try:
        user_doc = users_container.read_item(item=user_id, partition_key=user_id)
    except CosmosResourceNotFoundError:
        # If not found, create user document
        user = {
            "id": user_id,
            "clientId": user_id,
            "email": email,
            "displayName": displayName,
            "signupDate": datetime.utcnow().isoformat()
        }
        user_doc = users_container.create_item(body=user)


    def count_query(container):
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.clientId = @clientId"
        params = [{"name": "@clientId", "value": user_id}]
        return list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))[0]

    farms_count = count_query(farms_container)
    images_count = count_query(images_container)
    jobs_count = count_query(jobs_container)
    
    return {
        "clientId": user_doc["clientId"],
        "email": user_doc["email"],
        "farmsCount": farms_count,
        "imagesCount": images_count,
        "totalProcessingJobs": jobs_count,
        "signupDate": user_doc["signupDate"]
    }
