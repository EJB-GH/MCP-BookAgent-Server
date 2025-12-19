#!/bin/bash

#setup venv, install req and uv
echo "Creating virtual environment..."
python -m venv venv
source .venv/bin/activate
pip install uv
uv init

echo "Installing requirements..."
uv add -r requirements.txt
echo "Enviroment Completed...run activatation command"

