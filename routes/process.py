from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import time
import uuid
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from helpers.container_launcher import start_processing_container

router = APIRouter()

class ProcessRequest(BaseModel):
    clientId: str
    farmId: str
    indices: List[str]

class ProcessingJob(BaseModel):
    id: str
    clientId: str
    farmId: str
    indices: List[str]
    status: str
    progress: int
    startTime: str
    endTime: Optional[str] = None

@router.post("/process", response_model=ProcessingJob)
def start_processing_job(payload: ProcessRequest, request: Request):
    jobs_container = request.app.state.jobs_container

    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    job = ProcessingJob(
        id=job_id,
        clientId=payload.clientId,
        farmId=payload.farmId,
        indices=payload.indices,
        status="processing",
        progress=0,
        startTime=now
    )

    jobs_container.create_item(body=job.dict())

    # Launch processing container
    start_processing_container(
        request.app,
        client_id=payload.clientId,
        farm_id=payload.farmId,
        job_id=job_id,
        vegetation_index=payload.indices[0]  # assuming only VARI for now
    )

    return job

@router.get("/status", response_model=ProcessingJob)
def get_job_status(clientId: str, farmId: str, request: Request):
    jobs_container = request.app.state.jobs_container

    # Get the latest job for this clientId + farmId combo
    query = """
    SELECT * FROM c 
    WHERE c.clientId = @clientId AND c.farmId = @farmId
    ORDER BY c.startTime DESC
    OFFSET 0 LIMIT 1
    """
    params = [
        {"name": "@clientId", "value": clientId},
        {"name": "@farmId", "value": farmId}
    ]

    results = list(jobs_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    ))

    if not results:
        raise HTTPException(status_code=404, detail="No processing job found for this farm.")

    job_data = results[0]

    # Simulate progress
    current_progress = job_data.get("progress", 0)
    if current_progress < 100:
        job_data["progress"] = min(100, current_progress + 25)
        if job_data["progress"] == 100:
            job_data["status"] = "completed"
            job_data["endTime"] = datetime.utcnow().isoformat()
        else:
            job_data["status"] = "processing"

        # Update in DB
        jobs_container.replace_item(item=job_data["id"], body=job_data)

    return ProcessingJob(**job_data)
