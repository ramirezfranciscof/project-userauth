#!/bin/zsh
################################################################################
# Deploy the cluster in the right order
#
# You need kubectl installed and a connection to some local or remote
# cluster (for example, with `minikube start`)
#
################################################################################

# Start configuration settings
# (check with `kubectl get configmap`)
kubectl apply -f shared-configmap.yml

# Start secret configuration settings
# (check with `kubectl get secret`)
kubectl apply -f shared-secrets.yml

# Create the volume
# (check with `kubectl get pvc`)
kubectl apply -f postgres-volume.yml

# Start the postgres service
kubectl apply -f postgres-db.yml

# Start the userauth REST API service
kubectl apply -f userauth-api.yml

# See all objects created
kubectl get all

################################################################################
