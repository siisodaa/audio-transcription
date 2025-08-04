from pydantic import BaseModel
from typing import List, Optional,Dict
from datetime import datetime


class TranscripePayload(BaseModel):
    userId : str
    audioChunkPaths : List[str]

class TranscripeOutput(BaseModel):
    jobId : str

class TranscriptResult(BaseModel):
    jobId: str
    status: str
    transcriptText: Optional[str]
    createdAt: Optional[datetime]
    completedTime: Optional[datetime]
    chunkStatuses: Optional[Dict[str, str]] = None