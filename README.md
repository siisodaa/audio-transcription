# Audio Transcription Service

This project implements an audio transcription service that accepts jobs consisting of audio chunks and returns stitched transcripts. It is designed to simulate processing doctor-patient conversations using a mocked ASR service.

## Features

- Submit transcription jobs via REST API  
- Process audio chunks asynchronously using Redis queue  
- Handle flaky ASR service with retries and backoff  
- Enforce concurrency limit on ASR calls  
- Persist jobs and chunk status in MongoDB  
- Resume incomplete jobs on server restart  
- Simple web frontend for job submission and transcript viewing  

## Tech Stack

- **FastAPI** – REST API backend  
- **Redis** – Queue for background processing  
- **MongoDB** – Persistent storage  
- **ASR Mock Service** – Simulated speech recognition  
- **Bootstrap + Vanilla JS** – Frontend demo interface  

## API Endpoints

- `POST /transcript/transcribe` – Submit a new job  
- `GET /transcript/{jobId}` – Retrieve transcript and job status  
- `GET /transcript/search` – Search jobs by `userId` or `jobStatus`  

## Job Flow

1. Client submits job with `userId` and audio chunk paths  
2. Job and chunk metadata stored in MongoDB  
3. Each chunk is enqueued in Redis  
4. Worker processes each chunk and retrieves transcript from ASR  
5. Chunks are retried on failure (up to 3 times)  
6. Transcript is stitched and job is marked completed  
7. Client polls for job status or retrieves via `GET /transcript/{jobId}`  

## Running the Project

1. Start **MongoDB** and **Redis**  
2. Set environment variables in `.env`  
3. Run the project using the provided script:  
   ```bash
   ./run.sh
   ```  
   This starts both the backend and the ASR worker.

4. Open `frontend/index.html` in your browser to access the demo UI.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

## Notes

- The ASR service is simulated with latency and failure conditions  
- Designed to complete transcript responses in under 20s in the happy case  
- Can recover from process restarts and continue incomplete jobs  
