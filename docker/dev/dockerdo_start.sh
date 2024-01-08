#!/bin/zsh
################################################################################
# Restarts an already existing container.
#
# `-a`
#     attach to the container as it is being restarted.
#
# This script is not really used as long as the initialization of the container
# is performed using `--rm`, but is kept as reference.
#
################################################################################
docker start -a "container_userauth_dev"
################################################################################
