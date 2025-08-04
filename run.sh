#!/bin/bash

export PYTHONPATH=$(pwd)

source myvenv/bin/activate

echo "Starting backend..."
python3 main.py &

echo "Starting ASR worker..."
python3 worker/asr_worker.py &

wait
