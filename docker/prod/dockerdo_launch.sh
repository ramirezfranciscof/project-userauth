#!/bin/zsh
################################################################################
# Launches the container from the image.
#
# `--rm`
#     will delete the container after it is stopped
#
# `-it`
#     runs the container in interactive mode
#
# `-p <host_port>:<cont_port>`
#     Publishes the port so that it can be accessed by the host.
#
################################################################################
docker run \
    --rm -it -p 8888:8888 -p 8000:8000 \
    --name "container_userauth" "image_userauth:v0.1.0"
################################################################################
