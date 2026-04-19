@echo off
REM Setup and run Video Assembler

REM Go to script directory
cd /d "%~dp0"

REM Create virtual environment if it doesn't exist
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Verifying and installing dependencies...
pip install -r requirements.txt

REM Run the project
echo Running Video Assembler...
IF "%~1"=="" (
    python build_video.py script.conf
) ELSE (
    python build_video.py "%~1"
)
