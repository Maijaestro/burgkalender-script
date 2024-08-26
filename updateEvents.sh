#!/bin/bash

PROJECT_FOLDER="burgkalender-script"
REPO_URL="https://github.com/Maijaestro/burgkalender-script"

if [ -d "$PROJECT_FOLDER" ]; then
    echo "Project folder exists. Execute git pull."
    cd $PROJECT_FOLDER
    git pull
else
    echo "Project folder doesn't exists. Clone repository."
    git clone $REPO_URL $PROJECT_FOLDER
    cd $PROJECT_FOLDER
fi

# Create virtual environments
if [ ! -d "venv" ]; then
    echo "Create virtual environment."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activate virtual environment."
source venv/bin/activate

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Install requirements."
    pip install -r requirements.txt
fi

python3 bwcrawl.py
python3 transform2ical.py
