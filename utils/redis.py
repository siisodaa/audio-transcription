import redis.asyncio as redis
from models.redisModels import redisEnqueue
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

QUEUE_KEY = "transcription_queue"
DEDUP_SET_KEY = "transcription_queue_dedup"

async def enqueueJob(job: redisEnqueue):
    job_data = job.dict()
    dedup_id = f"{job.jobId}:{job.chunkPath}"

    if await r.sismember(DEDUP_SET_KEY, dedup_id):
        print(f"[DEDUP] Skipping already enqueued chunk {dedup_id}")
        return

    await r.rpush(QUEUE_KEY, json.dumps(job_data))
    await r.sadd(DEDUP_SET_KEY, dedup_id)
    print(f"[ENQUEUE] Enqueued {dedup_id}")

async def dequeueJob() -> redisEnqueue | None:
    try:
        raw_job = await r.lpop(QUEUE_KEY)
        if raw_job is None:
            return None

        job_data = json.loads(raw_job)

        if "jobId" not in job_data or "chunkPath" not in job_data:
            print("[ERROR] Invalid job format:", job_data)
            return None

        dedup_id = f"{job_data['jobId']}:{job_data['chunkPath']}"
        await r.srem(DEDUP_SET_KEY, dedup_id)

        return redisEnqueue(**job_data)
    except Exception as e:
        print("[ERROR] Failed to dequeue job:", e)
        return None
