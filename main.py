from fastapi import FastAPI, Path
from pydantic import BaseModel
from datetime import datetime
from typing import List
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",  # frontend dev server
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# profile model
class UserProfile(BaseModel):
    clientId: str
    email: str
    farmsCount: int
    imagesCount: int
    totalProcessingJobs: int
    signupDate: datetime

@app.get("/users/{user_id}/profile", response_model=UserProfile)
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

# farm model
class Farm(BaseModel):
    id: str
    clientId: str
    name: str
    createdAt: str
    imageCount: int

@app.get("/users/{user_id}/farms", response_model=List[Farm])
def get_user_farms(user_id: str):
    print(f"[API] Farms requested for: {user_id}")
    return [
        {
            "id": "farm001",
            "clientId": user_id,
            "name": "North Field",
            "createdAt": "2024-01-20",
            "imageCount": 12
        },
        {
            "id": "farm002",
            "clientId": user_id,
            "name": "South Field",
            "createdAt": "2024-01-22",
            "imageCount": 8
        },
        {
            "id": "farm003",
            "clientId": user_id,
            "name": "West Field",
            "createdAt": "2024-01-25",
            "imageCount": 6
        }
    ]