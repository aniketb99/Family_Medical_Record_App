#!/bin/bash

# This script sets up the environment for the Family Medical Record App

# Update package list
sudo apt update

# Install Python, venv, pip, and git
sudo apt install -y python3 python3-venv python3-pip git

# Clone the repository
# Replace <your-repo-url> with the actual repository URL
# git clone <your-repo-url>

# Navigate to the project directory
cd Family_Medical_Record_App

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install required Python packages
python -m pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
