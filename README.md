# UserAuth

UserAuth is a python-based user authentication REST-API server for automated celebrity recognition.

It allows users to register to the service, and then access their data and their logins to the system at any time.
Users can also update their username and delete their account (and all information associated with it) whenever they want.
Normal users can be upgraded to celebrity users by providing a photo of themselves to be analized by a ML face recognition model.

NOTE: This rest-api was developed for an interview process in which the company provided an AI model to identify celebrities.
In order to share only my work and not the code provided by the company, the model is currently replaced by a placeholder class that just returns a name and percentage as indicated by the caller.

## Installation

### Local install:

UserAuth is distributed as a python library, so it can be easily installed with pip inside a virtual environment.

```console
(test-venv) user@computer:~$ pip install .
```

Using an editable install and the develop dependencies is optional, but useful for development(replace the last `.` by `-e .[dev]`).

### Docker container:

For an even more isolated environment, one can quickly build a docker image and start up a quick simple test container by running:

```console
user@computer:~$ docker build -f docker/prod/Dockerfile -t "image_userauth:v0.1.0" .
user@computer:~$ docker run -it -p 8000:8000 --name "container_userauth" "image_userauth:v0.1.0"
```

This test instance will not allow you to persist any data once you delete the container.
However, it is quite easy to use an alternate image and/or modify the options provided to `docker run` in order to obtain a more versatile container.
For more information about this, check the instructions in `docker/README.md`.

### Kubernetes deployment:

Finally, if you have access to a kubernetes cluster, we also provide with the helm charts necessary to start a deployment.
Providing any "quick-deploy" instructions here is a bit more complicated (since data sharing/persistence in kubernetes is not trivial to set up).
Please check the `kubernetes/README.md` file for more details about this kind of installation.

## Usage

Once you have installed the package, `UserAuth` comes with its own minimalistic command line interface that allows you to start the server by running `userauth server start`.
If you opted for one of the options that rely on the production docker image, the command is executed automatically when the container starts.

The other important command that is important to know is the `makeadmin`, that allows you to give the admin role to a user:

```console
(python-env) user@computer:~$ userauth database makeadmin <username>
```

### Database Backend

Starting the server will automatically connect to the database backend.
By default, `UserAuth` will use an SQLite database located at its root directory (that is created and configured, if it didn't already exist).
This facilitates significantly running small demos and tests of the API.
However, it also has the option of connecting to an external postgres service for better scalability and data persistence.
This needs to be indicated via the environment variables accessible in the environment, which will indicate what kind of database to use as well as the credentials (see table below).

| ENV VAR NAME      | DEFAULT | DESCRIPTION |
| :---------------- | :------ | :---------- |
| DEPLOYMENT_TYPE   |  'DEV'  | 'DEV': create and use a local SQLite database<br> 'PROD': connect to an pre-existing postgres instance|
| POSTGRES_USERNAME |  None   | Username for the pre-existing postgres instance |
| POSTGRES_PASSWORD |  None   | Password for the pre-existing postgres instance |
| POSTGRES_HOST     |  None   | Host for connecting to pre-existing postgres instance |
| POSTGRES_PORT     |  None   | Port for connecting pre-existing postgres instance |
| POSTGRES_DBNAME   |  None   | Name of the database in the postgres instance |

Note that in the case of the postgres database, `UserAuth` will not create neither the database nor the table.
It will use directly the table provided in the `POSTGRES_DBNAME` variable (initializing it the first time, if it was a blank table).

If you opted for one of the options that rely on the production docker image, these environment variables need to be passed to the container when executing the `docker run` command.

### Resources and Endpoints

In order to access any of the resources offered by a `UserAuth` REST-API deployment, one needs to (1) have an account and (2) authenticate with the correct credentials.
There are two public endpoints that implement the HTTP POST method in order to take care of these tasks:

 - `/user` (POST): used to sign up a new user to the service, which is assigned the default normal role.
 The celebrity role can be enabled by validating a picture (see below), and the admin role can only be granted by other admins or through the command line interface (`userauth database makeadmin <username>`).
 - `/token` (POST): used to obtain a JWT by providing the credentials (username and password) for an existing user.
 This token has to be used in the header of any future requests to other endpoints as proof of the identity of the requester.
 Tokens created this way are valid for a period of 30 minutes.

**USER**

This is both the main resource exposed by the API and the authentication mechanism.
It contains the information of the user such as name, surname, username, email and role.
Each user also gets assigned a specific UUID once it is registered by the service.
The endpoints related to user resources are:

 - `/user` (GET): this endpoint can only be used by users with admin role to get a list of all available users in the system.
 The endpoint also implements the POST method as described above.
 - `/user/<UUID>` (GET): This grants access to the data of a specific user identified by its UUID.
 Users only have access to their own data, except for admin roles which can see any user.
 A shortcut to the endpoint with your own UUID can be found at `/user/me`.
 - `/user/<UUID>` (PATCH): Allows to change the username and role of a specific user.
 Users can change their own username, and admin roles can modify both usernames and roles.
 - `/user/<UUID>` (DELETE): Deletes the user from the database and all data associated with it (including login information, see below).
 Only users can delete their own data: not even admin roles can delete other users.
 - `/user/<UUID>/validate_photo` (POST): It allows user to update their role to celebrity by providing a photo of themselves.
 The photo is automatically analized by a ML face recognition model in order to validate that the celebrity is recognized and name / surname match.

**LOGINS**

Every time a user successfully uses the `/token` endpoint to authenticate, a record of the login is kept in the database.
Users can obtain a list of their login records by the following endpoints (all implementing the GET method):

 - `/user/me/logins`
 - `/user/<UUID>/logins`

Login records also have their own UUIDs, and individual login records can be obtained by using any of the following GET endpoints:

 - `/logins/<LOGIN_UUID>`
 - `/user/me/logins/<LOGIN_UUID>`
 - `/user/<USER_UID>/logins/<LOGIN_UUID>`

Again, non-admin roles only have access to their own login records, but admin roles can also see the login records of other users.
Additionally, admin roles have access to the general `/logins` GET endpoint which returns all successful logins to the system.

**API DOCUMENTATION**

The `UserAuth` REST-API also generates endpoints for access to its own documentation.
By going to the `/docs` endpoint, one has access to a swagger web interface that can be used to interact directly with the server.
The `/redocs` endpoint contains the same information but in a static non-interactive format.
Finally, the openAPI json can be obtained from the `/openapi.json` endpoint, but we are also including a copy of it here in the package.
