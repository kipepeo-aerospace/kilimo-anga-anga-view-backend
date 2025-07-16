from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import time
from helpers.container_launcher import start_processing_container
from fastapi import Request  # if not already imported


router = APIRouter()

# In-memory store for mock jobs
jobs: Dict[str, dict] = {}

class ProcessRequest(BaseModel):
    clientId: str
    farmId: str
    indices: List[str]

class ProcessingJob(BaseModel):
    id: str
    clientId: str
    farmId: str
    indices: List[str]
    status: str  # pending | processing | completed | failed
    progress: int
    startTime: str
    endTime: Optional[str] = None

@router.post("/process", response_model=ProcessingJob)
def start_processing_job(payload: ProcessRequest, request: Request):
    job_id = f"job-{int(time.time())}"
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

    # Keyed by clientId + farmId for easy lookup
    job_key = f"{payload.clientId}:{payload.farmId}"
    jobs[job_key] = job.dict()

    # Trigger the Azure container: Enter the PIPELINE
    start_processing_container(
        request.app,
        client_id=payload.clientId,
        farm_id=payload.farmId,
        job_id=job_id,
        vegetation_index=payload.indices[0] # forcing VARI computation as that is what the pipeline does for now
    )

    return job


@router.get("/status", response_model=ProcessingJob)
def get_job_status(clientId: str, farmId: str):
    job_key = f"{clientId}:{farmId}"
    job_data = jobs.get(job_key)

    if not job_data:
        raise HTTPException(status_code=404, detail="No processing job found for this farm.")

    # Simulate progress increase
    current_progress = job_data['progress']
    if current_progress < 100:
        job_data['progress'] = min(100, current_progress + 25)
        if job_data['progress'] == 100:
            job_data['status'] = 'completed'
            job_data['endTime'] = datetime.utcnow().isoformat()
        else:
            job_data['status'] = 'processing'

    jobs[job_key] = job_data
    return ProcessingJob(**job_data)
