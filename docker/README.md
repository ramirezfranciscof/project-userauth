# UserAuth - Docker config

This folder contains the files to generate docker images for deploying UserAuth in containers.
The `prod` folder contains the files for building the image to be used in production, while the `dev` folder has the same but for a development environment (including some scripts and docker-compose for testing deployment).

## How to use this image

The production image can be generated very easily by running the following command inside of the `docker/prod` folder:

```console
user@computer:~$ docker build -f ./Dockerfile -t "image_userauth:v0.1.0" ../../.
```

Note that this will generate an image named `image_userauth` with version `v0.1.0`.
These can be modified, but then all the remaining scripts here and in the `kubernetes` folder will have to be adapted accordingly.

Once the `UserAuth` image is created, there are several options that need to be provided in order to be able to use it effectively.
The most important one is making the app available outside the container by exposing the port `8000`, in which the image starts the REST-API service.
Therefore, the most basic startup command will be:

```console
user@computer:~$ docker run -it -p 8000:8000 --name "container_userauth" "image_userauth:v0.1.0"
```

However, the default settings of the `UserAuth` application will create and use an SQLite database inside the container.
This simplifies test deployments but prevents any sort of data persistence or scalability of service.
The data persistence can be solved by mounting a volume to save the SQLite database in (see the "development environment" below), but this does not deal with scalability.

For more scalable and robust deployments, the `UserAuth` application can also use an existing external postgres service.
In order to know which type of database to use, as well as to get the credentials for the postgres service, the application will read the environment variables in the container.
The relevant variables are in the following table:

| ENV VAR NAME      | DEFAULT | DESCRIPTION |
| :---------------- | :------ | :---------- |
| DEPLOYMENT_TYPE   |  'DEV'  | 'DEV': create and use a local SQLite database<br> 'PROD': connect to an pre-existing postgres instance|
| POSTGRES_USERNAME |  None   | Username for the pre-existing postgres instance |
| POSTGRES_PASSWORD |  None   | Password for the pre-existing postgres instance |
| POSTGRES_HOST     |  None   | Host for connecting to pre-existing postgres instance |
| POSTGRES_PORT     |  None   | Port for connecting pre-existing postgres instance |
| POSTGRES_DBNAME   |  None   | Name of the database in the postgres instance |

Although one could manually start the postgres service and provide these variables when executing the `docker run` command, using these in automated deployment tools is the more typical case.
The instructions on how to use the image in a kubernetes cluster can be found on the `kubernetes` folder.

## The development environment

Besides the `prod` image for production deployments, we have also included a `dev` image for development and testing.
While the first one directly launches the `UserAuth` application, the development one will launch a `jupyter-lab` at startup instead.
This provides a useful interface that makes it very easy to interact with the contents of the container.

The development image can be built by running the following command in the `docker/dev` folder:

```console
user@computer:~$ docker build -f ./Dockerfile -t "image_userauth_dev:v0.1.0" ../../.
```

And then a container can be started with:

```console
user@computer:~$ docker run \
    -v $(pwd)/../..:/home/root/app \
    --rm -it -p 8888:8888 -p 8000:8000 \
    --name "container_userauth_dev" "image_userauth_dev:v0.1.0"
```

The previous setup will not only expose the ports 8000 and 8888 (one for the REST-API and the other for the jupyter interface), but will also mount inside the container the files that are in the host (so any change to the codebase will persist).
As a final detail, it also uses `--rm` to automatically remove the container when it exits (so that the python environment is always re-created from scratch).

Note that this time the `UserAuth` REST-API is not immediately started: the container just provides the right environment.
You need to log into it (via a terminal in the jupyter interface, for example) and run `userauth server start`.

The `docker/dev` also contains a `docker-compose.yml` file which allows to try out the development image in a more complex deployment setup.
Besides running the app in a container, it will also start a separate postgres container and will set up the environment variables in order to connect to said instance.
It will still not set up the `DEPLOYMENT_TYPE = PROD`, but that can be easily done inside the container before starting the server.

To run this test deployment it just execute `docker-compose up` while inside the `docker/dev` folder.
