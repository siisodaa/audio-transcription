from pydantic import BaseModel


class redisEnqueue(BaseModel):
    jobId : str
    chunkPath : str