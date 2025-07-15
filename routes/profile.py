from fastapi import APIRouter, Path
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class UserProfile(BaseModel):
    clientId: str
    email: str
    farmsCount: int
    imagesCount: int
    totalProcessingJobs: int
    signupDate: datetime

@router.get("/users/{user_id}/profile", response_model=UserProfile)
def get_user_profile(user_id: str = Path(..., description="The user's display name from Entra")):
    print(f"[API] Profile requested for: {user_id}")
    return {
        "clientId": user_id,
        "email": f"{user_id}@kilimo.com",
        "farmsCount": 3,
        "imagesCount": 48,
        "totalProcessingJobs": 12,
        "signupDate": "2024-09-01T12:00:00Z"
    }
