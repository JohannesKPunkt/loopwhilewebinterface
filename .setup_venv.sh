#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the directory of this script
cd "$SCRIPT_DIR"

# Import settings
source .settings.sh

# Remove existing venv (if any)
rm -rf "$LW_VENV_NAME"

# Create new venv
virtualenv -p python3 "$LW_VENV_NAME"

# Enter venv
source "$LW_VENV_NAME/bin/activate"

# Install python dependencies
pip3 install TurboGears2 genshi transaction waitress autobahn[twisted,accelerate]

# Leave venv
deactivate
