#!/bin/bash
# Creates a docker container that runs the lw service and nginx

mkdir -p logs/loopwhile
mkdir -p logs/nginx
mkdir -p logs/supervisor
docker build --tag loopwhile .
