#!/bin/bash
cd /opt/uniforma/backend
source venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 9100
