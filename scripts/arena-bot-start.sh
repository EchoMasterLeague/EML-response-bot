#!/usr/bin/env bash
SCRIPTS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd -P )
PROJECT_DIR=$(dirname "$SCRIPTS_DIR")
VRARENA_DIR=$PROJECT_DIR/src/eml-bot-arena
WORKING_DIR=$(pwd)

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

echo "# EML Arena Discord Bot #"
echo "Project Directory: $PROJECT_DIR"
echo "Scripts Directory: $SCRIPTS_DIR"
cd "$PROJECT_DIR" || die $EXIT_CODE_PROJECT_DIR "Failed to change directory to $PROJECT_DIR"

echo "Removing Cache..."
find .. -type d -name '__pycache__' | while read cache; do echo $cache; rm -rf $cache; done

echo "Pulling latest changes..."
git pull || echo "WARNING: Failed to pull latest changes"

# VENV
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating Virtual Environment..."
    python3 -m venv "$PROJECT_DIR/venv" || die $EXIT_CODE_VENV_DIR "Failed to create Virtual Environment"
fi


echo "Activating Virtual Environment..."
source "$PROJECT_DIR/venv/bin/activate" || die $EXIT_CODE_VENV_START "Failed to activate Virtual Environment"

echo "Installing dependencies..."
pip install -r requirements.txt || die $EXIT_CODE_DEPENDENCIES "Failed to install dependencies"

echo "Starting Arena Bot..."
cd "$VRARENA_DIR" || die $EXIT_CODE_VRARENA_DIR "Failed to change directory to $VRARENA_DIR"
python main.py || die $EXIT_CODE_START_BOT "Failed to start Arena Bot"

# Return to the initial working directory
die $EXIT_CODE_NORMAL "Arena Bot stopped successfully."