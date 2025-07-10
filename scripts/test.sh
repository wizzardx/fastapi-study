#!/bin/bash
source venv/bin/activate
# mypy --strict main.py
fastapi dev main.py
