#!/bin/bash
# Setup and run Video Assembler

# Go to script directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Verifying and installing dependencies..."
pip install -r requirements.txt

# Run the project
echo "Running Video Assembler..."
if [ -z "$1" ]; then
    python build_video.py script.conf
else
    python build_video.py "$1"
fi
