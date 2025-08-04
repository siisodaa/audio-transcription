Audio Transcription Service

This project implements an audio transcription service for doctor-patient conversations. Clients submit jobs with audio chunks, and the system returns a stitched transcript.

Features

Submit transcription jobs via REST API

Process audio chunks asynchronously using a Redis queue

Handle flaky ASR service with retries and exponential backoff

Enforce concurrency limit on ASR requests

Persist jobs and chunks in MongoDB

Resume incomplete jobs on server restart

Simple web frontend for submitting jobs and viewing transcripts

Tech Stack

FastAPI – REST API backend

Redis – Job queue

MongoDB – Persistent storage

ASR Mock Server – Simulated transcription service

Bootstrap + Vanilla JS – Frontend demo interface

API Endpoints

POST /transcript/transcribe – Submit a new transcription job

GET /transcript/{jobId} – Fetch transcript and status

GET /transcript/search – Search jobs by userId or jobStatus

Job Lifecycle

Client submits a job with userId and chunk paths

Metadata saved in MongoDB

Chunks enqueued in Redis

Worker fetches chunks and sends them to ASR

On success or retries exhausted, job is marked complete

Transcript is stitched and saved

Running the Project

Ensure the following services are running:

Redis

MongoDB

ASR mock server

Start the backend and worker:

./run.sh

Open index.html in your browser to use the demo frontend

Setup

Install Python dependencies:

pip install -r requirements.txt

Create a .env file with your MongoDB connection string:

MONGO_URI=mongodb://localhost:27017

