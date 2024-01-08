#!/bin/zsh
################################################################################
# Builds the image.
#
# `-f`
#     will use the dockerfile file specified.
#
# `../../.` (context)
#     so that it has access to the source files in parent dir.
#
################################################################################
docker build -f ./Dockerfile -t "image_userauth:v0.1.0" ../../.
################################################################################
