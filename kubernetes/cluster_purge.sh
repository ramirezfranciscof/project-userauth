#!/bin/zsh
################################################################################
# Shut down the cluster
################################################################################

# Shut down the services running
kubectl delete -f userauth-api.yml
kubectl delete -f postgres-db.yml

kubectl delete secret shared-secrets
kubectl delete configmap shared-configmap
kubectl delete pvc postgres-pv-claim
kubectl delete pv postgres-pv-volume

# See all objects created
kubectl get all

################################################################################
