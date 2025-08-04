import asyncio
import json
import httpx
import traceback
from datetime import datetime, timezone
from bson import ObjectId
from utils.redis import dequeueJob, enqueueJob
from config.db import connect
from models.redisModels import redisEnqueue
import random

ASR_ENDPOINT = "http://localhost:3000/get-asr-output"
MAX_RETRIES = 3
SEMAPHORE = asyncio.Semaphore(100)

db = connect()
jobs_collection = db["jobs"]
chunks_collection = db["job_chunks"]

async def call_asr(chunkPath: str):
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(ASR_ENDPOINT, params={"path": chunkPath})
            return response
        except Exception:
            print(f"[ASR ERROR] Failed to call ASR for {chunkPath}")
            traceback.print_exc()
            return None

async def process_single_chunk(jobId: str, chunkPath: str):
    async with SEMAPHORE:
        chunk = await chunks_collection.find_one({"jobId": jobId, "chunkPath": chunkPath})
        if not chunk:
            print(f"[WARN] Chunk not found for {chunkPath}")
            return

        retries = chunk.get("retries", 0)
        response = await call_asr(chunkPath)

        if not response or response.status_code != 200:
            if retries + 1 >= MAX_RETRIES:
                await chunks_collection.update_one(
                    {"_id": chunk["_id"]},
                    {"$set": {"status": "failed", "errorMessage": "ASR failed after retries"}}
                )
                print(f"[FAILURE] Giving up on chunk {chunkPath}")
            else:
                backoff_delay = min(2 ** retries, 10)
                """ a little jitter for randomness """
                jitter = random.uniform(0.5, 1.5) 
                await chunks_collection.update_one(
                    {"_id": chunk["_id"]},
                    {"$set": {"status": "retrying"}, "$inc": {"retries": 1}}
                )
                await asyncio.sleep(backoff_delay + jitter) 
                await enqueueJob(redisEnqueue(jobId=jobId, chunkPath=chunkPath))
                print(f"[RETRY] Re-enqueued chunk {chunkPath} for retry after {backoff_delay}s")
            return

        try:
            data = response.json()
            transcript = data.get("transcript", "")
        except Exception:
            await chunks_collection.update_one(
                {"_id": chunk["_id"]},
                {"$set": {"status": "failed", "errorMessage": "Invalid ASR response"}}
            )
            print(f"[ERROR] Invalid JSON response for chunk {chunkPath}")
            return

        await chunks_collection.update_one(
            {"_id": chunk["_id"]},
            {"$set": {"status": "success", "transcript": transcript}}
        )
        print(f"[SUCCESS] Transcribed {chunkPath}")

async def process_full_job(jobId: str):
    job_doc = await jobs_collection.find_one({"jobId": jobId})
    if not job_doc:
        print(f"[SKIP] Job {jobId} not found in DB")
        return
    if job_doc.get("status") == "completed":
        print(f"[SKIP] Job {jobId} is already completed")
        return

    print(f"[JOB] Processing job {jobId}")
    chunks = await chunks_collection.find({"jobId": jobId, "status": {"$in": ["pending", "retrying"]}}).to_list(length=None)
    tasks = [process_single_chunk(jobId, chunk["chunkPath"]) for chunk in chunks]
    await asyncio.gather(*tasks)

    remaining = await chunks_collection.count_documents(
        {"jobId": jobId, "status": {"$in": ["pending", "retrying"]}}
    )

    if remaining == 0:
        full_transcript = ""
        success_chunks = chunks_collection.find({"jobId": jobId, "status": "success"})
        async for doc in success_chunks:
            full_transcript += doc.get("transcript", "") + "\n"

        await jobs_collection.update_one(
            {"jobId": jobId},
            {"$set": {
                "status": "completed",
                "transcriptText": full_transcript.strip(),
                "completedTime": datetime.now(timezone.utc)
            }}
        )
        print(f"[COMPLETE] Job {jobId} completed")

async def resume_incomplete_jobs():
    print("[RESUME] Checking for incomplete jobs...")
    jobs = await jobs_collection.find({"status": {"$ne": "completed"}}).to_list(length=None)
    for job in jobs:
        jobId = job["jobId"]
        chunks = await chunks_collection.find({
            "jobId": jobId,
            "status": {"$in": ["pending", "retrying"]}
        }).to_list(length=None)
        for chunk in chunks:
            await enqueueJob(redisEnqueue(jobId=jobId, chunkPath=chunk["chunkPath"]))
            print(f"[RESUME] Re-enqueued chunk {chunk['chunkPath']} of job {jobId}")

async def worker_loop():
    print("[START] ASR worker loop started")
    await resume_incomplete_jobs()
    while True:
        job = await dequeueJob()
        if job is None:
            await asyncio.sleep(1)
            continue
        await process_full_job(job.jobId)

if __name__ == "__main__":
    asyncio.run(worker_loop())
