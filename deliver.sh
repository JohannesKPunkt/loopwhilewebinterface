#!/bin/bash

USER="loopwhile"
GROUP=$USER
INSTALL_DIR="/opt/loopwhile/"
USER_SRC_DIR="/tmp/loopwhile_user_src/"
HTTPD_DIR="/var/www/html/"

#TODO deliver run.sh, lwre

echo "copy python sources"
cp -r src/ "$INSTALL_DIR/"
chown $USER:$GROUP "$INSTALL_DIR/src/."

echo "copy templates"
cp -r templates/ "$INSTALL_DIR/"
chown $USER:$GROUP "$INSTALL_DIR/templates/."

echo "build tutorial"
python3 src/TutorialGenerator.py --infile=$INSTALL_DIR/templates/tutorial.template --outfile=$INSTALL_DIR/templates/tutorial_container.xml

echo "copy web dir"
cp -r web/ $HTTPD_DIR

echo "create user source dir if not existent"
mkdir -p $USER_SRC_DIR
chown $USER:$GROUP $USER_SRC_DIR
