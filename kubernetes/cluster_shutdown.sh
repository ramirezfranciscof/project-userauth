#!/bin/zsh
################################################################################
# Shut down the cluster
################################################################################

# Shut down the services running
kubectl delete -f userauth-api.yml
kubectl delete -f postgres-db.yml

# See all objects created
kubectl get all

################################################################################
