# Deploy Feature Factory

A variety of resources facilitate easy deployment of Feature Factory:
- `Makefile` to manage all resources
- `docker`
- `docker-compose`, for actual deployment of Hub, User, and DB containers
- shell utilities
    - create/delete users
    - use LetsEncrypt to generate SSL certificate
- configuration files

## Installation

1. Install [Docker Engine](https://docs.docker.com/engine/installation/) and [Docker Compose](https://docs.docker.com/compose/install/) on your system.

2. Download the FeatureFactory repository.
    ```
    git clone https://github.com/HDI-Project/FeatureFactory.git
    ```

## Configuration

Feature Factory allows configuration in several places.

### App Deployment


Default app configuration variables are provided in `deploy/.env`.

To override any of these defaults, set these variables in a new file `deploy/.env.local`.

Definitely override values for these variables:

- `FF_DOMAIN_NAME`: fully-qualified domain name of this server, used for Let's Encrypt.
- `FF_DOMAIN_EMAIL`: email associated with domain name registration
- `MYSQL_ROOT_PASSWORD`: password for DB root user

You can usually leave these variables at their default values:

- `DOCKER_NETWORK_NAME`: name for docker network used for networking containers
- `HUB_IMAGE_NAME`: name for docker Hub image
- `HUB_CONTAINER_NAME`: name for docker Hub container
- `FF_IMAGE_NAME`: name for docker User notebook server image
- `FF_CONTAINER_NAME`: prefix for docker User containers. Actual containers will have
    `-username` appended.
- `FF_DATA_DIR`: path to data directory on *host machine* (deployment machine)
- `FF_PROJECT_NAME`: name for docker-compose app
- `MYSQL_CONTAINER_NAME`: name for docker DB container
- `MYSQL_ROOT_USERNAME`: username for DB root user
- `MYSQL_DATABASE`: competition database name in DB
- `MYSQL_DATA_VOLUME_NAME`: name for DB data volume
- `SECRETS_VOLUME_NAME`: name for Hub secrets volume

### Userlist

*Currently, this method does not allow setup of template notebooks and DB credentials. Thus,
it should be avoided entirely in favor of [User and data
management](#user-and-data-management).*

Optionally, you can provide a userlist in `deploy/userlist`. Include one user per row.

- Specify normal users by their username only: `testuser`
- Specify admin users by appending an indicator: `adminuser admin`

### Jupyterhub and Jupyter Notebook

You may want to modify the default `deploy/jupyterhub_config.py` file. However, you should
know what you're doing to not break things.

## Build the app

Build the necessary docker images.
```
make build
```

## Launch the app

Launch the app.
```
make up
```

## User and data management

Users can be added or deleted using `deploy/add_user.sh` and `deploy/delete_user.sh`. These
commands create user accounts on the hub container, setup notebooks templates, and setup
authentication for each user with the DB.

Most files are stored directly on the host machine and mounted in the Hub and User
containers:
- Experiment data: `FF_DATA_DIR/data`
- Notebooks and other user-created files: `FF_DATA_DIR/users`
- Configuration files for FeatureFactory and JupyterHub: `FF_DATA_DIR/config`

The MySQL database is mounted on a docker data volume:
- `db-data`

## App administration

Admins can perform administrative tasks with respect to the Feature Factory app as well as
the Feature Factory data science experiment. Admin users can manage and organize an
experiment without needing access to the host machine.

Create an admin user using `add_user.sh -a admin_username admin_password`.

App admin
- Can log into JupyterHub via the admin web interface and add/remove users, restart/shutdown
    notebooks, and more.
- Can also create/remove users from the host machine command line using `add_user.sh` and
    `delete_user.sh`.
- Can modify the experiment database.

Experiment admin
- Can log into JupyterHub and use the `notebooks/admin/Admin.ipynb` notebook to initialize
    experiments, restart experiments, and view features created.
- To create an experiment, the admin user must store data on the server, then execute
    Python commands to initialize the experiment and database, provide paths to the
    experiment data, and configure experiment parameters.

## Manage app lifecycle

The available tasks can be viewed with
```
make help
```

### Restarting the server

You may want to restart the server to modify configuration of JupyterHub, update the
Feature Factory code, or some other reason.

Stop the app. This stops, but does *not* remove, the hub, user, and DB containers. Note that hub
state files, user notebooks, and the database dump persist on the filesystem or in data
volumes.
```
make stop
```

Restart the app.
```
make start
```

Down the app. This stops and removes the hub, user, and database containers. Note that hub
state files persist, user notebooks, and the database dump persist on the filesystem.
```
make down
```

*Optional*: Clean filesystem and containers. This stops and removes all Feature Factory
containers, if not been already done. Additionally, user notebooks and config files are
removed. Note that this *does not clear the database*, which may then retain information
relating to non-existent users and expect user credentials that have been deleted.
```
make clean
```

*Optional*: Clean images, network, and volumes, in addition to filesystem and containers.
This removes all trace of Feature Factory beside the source repository and the experiment
data directory. Built images are removed, the docker internal network is shut down, and the
database volume is removed.
```
make clean_all
```
