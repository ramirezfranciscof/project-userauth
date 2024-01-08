# UserAuth - Kubernetes deployment

This folder contains the files to deploy the application in a Kubernetes cluster.
It is a prerequisite to have a local docker image for UserAuth (`image_userauth:v0`) installed in said cluster.

The deployment was designed to be able to scale the number of REST-API services, while maintaining data persistence through a local volume in the cluster.
A single postgres service is used to centrally manage this persistent database.

## Cluster deployment

To start the deployment, one must first load the required configurations that are shared between the different services.

```console
user@computer:~$ kubectl apply -f shared-configmap.yml
```

One also must load the secrets (username and password for the database).
We provide here a template with an example username and password, but the user is encouraged to change these variables before loading them to the cluster.

```console
user@computer:~$ kubectl apply -f shared-secrets.yml
```

Both the `configmap` and the `secrets` can be checked by running `kubectl get configmap` or `kubectl get secret`.

Before deploying the database service, one needs to have an available volume in where to store the data.
We include a helm chart for volume creation and claim here designed to be used in a `minikube` test cluster (see below), but the user will want to customize these for their production cluster.

```console
user@computer:~$ kubectl apply -f postgres-volume.yml
```

The creation of the volume and the claim can be checked by running `kubectl get pv` and `kubectl get pvc`.
If they were generated successfully, one can then proceed to deploy the database service:

```console
user@computer:~$ kubectl apply -f postgres-db.yml
```

Finally, the `UserAuth` REST-API service can be started by running:

```console
user@computer:~$ kubectl apply -f userauth-api.yml
```

To check the status of the deployed cluster, just run `kubectl get all` (or, alternatively, the more specific `kubectl get pod` or `kubectl get service`).
Information on a more specific element can be obtained by running `kubectl describe <object_type> <object_name>` (for example: `kubectl describe pod userauth-restapi-64675b95b6-l8n7j`)

The base configuration is set to have only 1 replica of the api running, but this can be easily scaled up by modifying the right entry on the `userauth-api.yml` helm chart:

```yaml
(...)
spec:
  replicas: 1
(...)
```

## Cluster shutdown

The services can be shut down by running:

```console
kubectl delete -f userauth-api.yml
kubectl delete -f postgres-db.yml
```

This will still leave the configurations and volumes (with the persisted data).
Deleting the data will, again, depend on how one is specifically handling the volumes.
But with the provided configuration, it will suffice to run:

```console
kubectl delete pvc postgres-pv-claim
kubectl delete pv postgres-pv-volume
```

Finally, to also remove the configuration setup of the `configmap` and the `secrets`:

```console
kubectl delete secret shared-secrets
kubectl delete configmap shared-configmap
```

## Simple test setup

One can use tools like `minikube` (see [here](https://minikube.sigs.k8s.io/docs/start/)) to easily start a local kubernetes cluster for testing purposes.
After installing the program (as well as the required container/VM manager) in one's specific OS system, the cluster can be started and stopped by using `minikube start` and `minikube stop`.

In the case of a `minikube` using docker as container manager, one has to be careful on how to make the `UserAuth` image available to the cluster.
One way to do this is to open a terminal and load the docker environment that is running inside the kubernetes cluster (which is, itself, inside a docker container).

```console
user@computer:~$ eval $(minikube docker-env)
```

After running this command, one can build the `UserAuth` image (see the `docker/README.md` instructions and `docker/prod` folder) and it will be accessible inside the cluster.
Note that the generated link to the docker inside the cluster only exists in this terminal, it is not a global change.
If a new terminal is open and the image needs to be rebuilt, the `eval` expression needs to be executed again.

As a final comment, when one is using this `minikube` setup, it is necessary to do a final step of exposing the REST-API service to the localhost by running:

```console
user@computer:~$ minikube service userauth-restapi-service
```
