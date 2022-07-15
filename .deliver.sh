#!/bin/bash

set -e

# Import settings
source .settings.sh

# Installation type (either "LOCAL" or "DOCKER")
install_type="$1"

echo "copy python sources"
cp -r src/ "$LW_INSTALL_DIR/"
chown $LW_USER:$LW_GROUP "$LW_INSTALL_DIR/src/."
chown $LW_USER:$LW_GROUP "$LW_INSTALL_DIR"

echo "copy templates"
cp -r templates/ "$LW_INSTALL_DIR/"
chown $LW_USER:$LW_GROUP "$LW_INSTALL_DIR/templates/."

echo "build tutorial"
python3 src/TutorialGenerator.py "--infile=$LW_INSTALL_DIR/templates/tutorial.template" "--outfile=$LW_INSTALL_DIR/templates/tutorial_container.xml"

echo "copy web dir"
cp -r web/* $LW_HTTPD_DIR

echo "create user source dir if not existent"
mkdir -p $LW_USER_SRC_DIR
chown $LW_USER:$LW_GROUP "$LW_USER_SRC_DIR/"

echo "create log dir if not existent"
mkdir -p $LW_LOG_DIR
chown $LW_USER:$LW_GROUP "$LW_LOG_DIR/"

echo "copy binary and scripts"
cp lwre "$LW_INSTALL_DIR/"
cp .settings.sh "$LW_INSTALL_DIR/"
cp run.sh "$LW_INSTALL_DIR/"
cp stop.sh "$LW_INSTALL_DIR/"
if [ "$install_type" == "DOCKER" ]
then
    cp .run_supervisor.sh "$LW_INSTALL_DIR/"
else
    cp .setup_venv.sh "$LW_INSTALL_DIR/"
fi
