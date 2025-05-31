#!/usr/bin/env bash

# This script is used to start the Arena Bot on linux compatible systems.
# It will pull the latest changes from the repository, create a Virtual Environment (if not exists),
# activate the Virtual Environment, install the dependencies, and start the Arena Bot.
# The script will stop the bot and exit the script if an error occurs.
# The script will return to the initial working directory before exiting.

# Directories
SCRIPTS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd -P )
PROJECT_DIR=$(dirname "$SCRIPTS_DIR")
VRARENA_DIR=$PROJECT_DIR/src/eml-bot-arena
WORKING_DIR=$(pwd)

# Exit Codes
EXIT_CODE_NORMAL=0
EXIT_CODE_SIGINT=1
EXIT_CODE_START_BOT=10
EXIT_CODE_DEPENDENCIES=50
EXIT_CODE_VENV_DIR=51
EXIT_CODE_VENV_START=52
EXIT_CODE_PROJECT_DIR=61
EXIT_CODE_VRARENA_DIR=62

# Function to stop the bot and exit the script
die() {
    echo "$2"
    # Return to the initial working directory
    if [ "$WORKING_DIR" != "$(pwd)" ]; then
        echo "Returning to initial working directory..."
        cd "$WORKING_DIR"
    fi
    exit $1
}
# Function to stop the bot when SIGINT signal is received
ctrl_c() {
    die $EXIT_CODE_SIGINT "Received SIGINT: Stopping Arena Bot..."
}
# Catch SIGINT signal (ctrl+c)
trap ctrl_c INT

log() {
    echo "[EML Arena Bot Startup] $1"
}

log "# EML Arena Discord Bot #"
log "Project Directory: $PROJECT_DIR"
log "Scripts Directory: $SCRIPTS_DIR"
cd "$PROJECT_DIR" || die $EXIT_CODE_PROJECT_DIR "Failed to change directory to $PROJECT_DIR"

log "Removing Cache..."
find . -type d -name '__pycache__' | sort -r | while read cache; do rm -rf $cache; done

log "Pulling latest changes..."
git pull || log "WARNING: Failed to pull latest changes"

# VENV
if [ ! -d "$PROJECT_DIR/venv" ]; then
    log "Creating Virtual Environment..."
    python3 -m venv "$PROJECT_DIR/venv" || die $EXIT_CODE_VENV_DIR "Failed to create Virtual Environment"
fi


log "Activating Virtual Environment..."
source "$PROJECT_DIR/venv/bin/activate" || die $EXIT_CODE_VENV_START "Failed to activate Virtual Environment"

log "Installing dependencies..."
pip install --upgrade --quiet -r requirements.txt || die $EXIT_CODE_DEPENDENCIES "Failed to install dependencies"

log "Starting Arena Bot..."
cd "$VRARENA_DIR" || die $EXIT_CODE_VRARENA_DIR "Failed to change directory to $VRARENA_DIR"
python main.py || die $EXIT_CODE_START_BOT "Failed to start Arena Bot"

# Return to the initial working directory
die $EXIT_CODE_NORMAL "Arena Bot stopped successfully."