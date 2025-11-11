#!/bin/bash
# Quick script to run the full pipeline
# Usage: ./summarize.sh

cd "$(dirname "$0")"
source venv/bin/activate
python run_pipeline.py
