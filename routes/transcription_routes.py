from fastapi import APIRouter, Request, Query,HTTPException
from models.transcriptModels import TranscripePayload, TranscripeOutput, TranscriptResult
from utils.redis import enqueueJob, dequeueJob
from models.redisModels import redisEnqueue
from uuid import uuid4
from datetime import datetime
import json 
from typing import List, Optional

router = APIRouter()

@router.post("/transcribe", response_model=TranscripeOutput)
async def create_new_job(request: Request, payload: TranscripePayload):
    db = request.app.state.db
    jobsCollection = db["jobs"]
    jobChunksCollection = db["job_chunks"]

    jobId = str(uuid4())
    now = datetime.utcnow()

    # job metadata
    await jobsCollection.insert_one({
        "jobId": jobId,
        "userId": payload.userId,
        "status": "pending",
        "transcriptText": "",
        "createdAt": now,
        "completedTime": None
    })

    # Process chunks
    for chunk in payload.audioChunkPaths:
        # Save to Mongo
        db_doc = {
            "jobId": jobId,
            "chunkPath": chunk,
            "status": "pending",
            "transcript": "",
            "retries": 0,
            "errorMessage": ""
        }

        await jobChunksCollection.insert_one(db_doc)

        # Enqueue to Redis
        redis_job = redisEnqueue(jobId=jobId, chunkPath=chunk)
        await enqueueJob(redis_job)

    return TranscripeOutput(jobId=jobId)


@router.get("/transcript/{jobId}", response_model=TranscriptResult)
async def get_transcript(jobId: str, request: Request):
    db = request.app.state.db
    jobs_collection = db["jobs"]
    chunks_collection = db["job_chunks"]

    job = await jobs_collection.find_one({"jobId": jobId})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    chunk_statuses = {}
    cursor = chunks_collection.find({"jobId": jobId})
    async for chunk in cursor:
        chunk_statuses[chunk["chunkPath"]] = chunk.get("status", "unknown")

    return TranscriptResult(
        jobId=job["jobId"],
        status=job.get("status", "unknown"),
        transcriptText=job.get("transcriptText"),
        createdAt=job.get("createdAt"),
        completedTime=job.get("completedTime"),
        chunkStatuses=chunk_statuses
    )

@router.get("/transcript/search", response_model=List[TranscriptResult])
async def search_transcripts(
    request: Request,
    jobStatus: Optional[str] = Query(None),
    userId: Optional[str] = Query(None)
):
    db = request.app.state.db
    jobs_collection = db["jobs"]

    # Build query
    query = {}
    if jobStatus:
        query["status"] = jobStatus
    if userId:
        query["userId"] = userId

    results = []
    cursor = jobs_collection.find(query)
    async for job in cursor:
        results.append(TranscriptResult(
            jobId=job["jobId"],
            transcriptText=job.get("transcriptText", ""),
            status=job["status"],
            createdAt=job["createdAt"],
            completedTime=job.get("completedTime")
        ))
    
    return results