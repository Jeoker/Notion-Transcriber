#!/bin/bash
sudo tailscale up --hostname=tiny-ai-logger
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
