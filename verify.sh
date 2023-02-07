#!/bin/sh
# This script is used to verify the integrity of the downloaded files using python docker image
# pinned to the required version

if ! [ -x "$(command -v docker)" ]
then
    echo "Docker could not be found"
    exit
fi

docker run --rm -v $(pwd):/data -w /data python:3.9-slim python3 verify.py $@
