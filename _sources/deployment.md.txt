# Deployment

A variety of resources facilitate easy deployment of FeatureHub:

- `Makefile` to manage all resources
- `docker`
- `docker-compose`, for actual deployment of Hub, User, and DB containers
- shell utilities
    - create/delete users
    - use LetsEncrypt to generate SSL certificate
- configuration files

## Installation

In this section, we walk through the steps to install FeatureHub on the host machine, build
Docker images, and spin up application containers. However, some of these steps will not
make sense until you have [configured](#configuration) the application as you desire. You
may want to go through these steps once to make sure everything runs okay, then update your
configuration file and re-build.

1. Install [Docker Engine](https://docs.docker.com/engine/installation/) and [Docker Compose](https://docs.docker.com/compose/install/) on your system.

1. Download the FeatureHub repository.
    ```bash
    git clone https://github.com/HDI-Project/FeatureHub.git
    ```

1. Ensure Python 3.5 is installed. 

    - On a virtual machine, one can use a system python.
        ```bash
        yum update -y
        yum install -y python35 python35-pip
        pip-3.5 install --upgrade pip
        ```

    - Otherwise, it is best to use a virtual environment, using `conda` for example:
        ```bash
        conda create -y -n featurehub python=3.5
        conda activate featurehub
        pip install --upgrade pip
        ```

1. Install Python requirements for the host.
    ```bash
    pip install -r deploy/requirements-host.txt
    ```

1. Create a local configuration.
    ```bash
    cd deploy
    perl -pe 's|XYZ|`openssl rand -hex 32`|g' .env.local.example > .env.local
    ```

1. Build the necessary docker images.
    ```bash
    make build
    ```

1. *(Optional)* Generate SSL certificate. This either generates a self-signed certificate
   using openssl or generates a certificate using LetsEncrypt, based on the
   `USE_LETSENCRYPT_CERT` configuration variable.
    ```bash
    make ssl
    ```

    ```eval_rst
    .. note::

        This Makefile target to generate certificates does not need to be re-executed unless you
        remove the Docker data volume, the certificates expire, or your domain configuration
        changes.
    ```

1. Launch the app.
    ```bash
    make up
    ```

At this point:
- you should have three running containers: a hub, a database, and a machine
  learning backend (eval server). Confirm that the output of `docker ps` shows these running
  containers.
- An unsecured login page should be visible at `http://localhost:8000` (not
  visible over the internet).
- You have not created any users, so no one will be able to login
  yet. See [User Management](#user-management) and [Data Management](#data-management) to
  continue.

Proceed to configure your app.

## Configuration

FeatureHub allows configuration in several places.

### App Deployment

Default app configuration variables are provided in `deploy/.env`.

To override any of these defaults, set these variables in a new file `deploy/.env.local`.

These variables are always needed and the app will break if not provided:

- `MYSQL_ROOT_PASSWORD`: password for DB root user
- `EVAL_API_TOKEN`: API token for eval server. You should generate a valid API token by
    executing `openssl rand -hex 32`.
- `HUB_CLIENT_API_TOKEN` : API token for Hub API client script. You should generate a valid
    API token by executing `openssl rand -hex 32`.

Definitely override values for these variables, as applicable (i.e. you are exposing app to
the internet or have enabled Discourse integration):

- `FF_DOMAIN_NAME`: fully-qualified domain name of this server, used for Let's Encrypt.
- `FF_DOMAIN_EMAIL`: email associated with domain name registration
- `DISCOURSE_DOMAIN_NAME` : domain name of the Discourse forum
- `DISCOURSE_CLIENT_API_USERNAME` : Username for Discourse admin, to use with Discourse API
    client. You must use the same username when setting up the Discourse instance.
- `DISCOURSE_CLIENT_API_TOKEN` : API token for Discourse API client. You should generate a
    valid API token by executing `openssl rand -hex 32`. You must use the same token when
    setting up the Discourse instance.

You can usually leave these variables at their default values:

- `DOCKER_NETWORK_NAME`: name for docker network used for networking containers
- `HUB_IMAGE_NAME`: name for docker Hub image
- `HUB_CONTAINER_NAME`: name for docker Hub container
- `HUB_API_PROT` : port for Hub REST API to list on
- `FF_IMAGE_NAME`: name for docker User notebook server image
- `FF_CONTAINER_NAME`: prefix for docker User containers. Actual containers will have
    `-username` appended.
- `FF_DATA_DIR`: path to data directory on *host machine* (deployment machine)
- `FF_PROJECT_NAME`: name for docker-compose app
- `FF_IDLE_SERVER_TIMEOUT`: timeout interval for idle servers (i.e., user containers). If a
    server is idle for this amount of time, then it will be automatically stopped. Due to some
    JupyterHub defaults, this value should be set to at least 5m 30s (`330`).
- `FF_CONTAINER_MEMLIMIT`: memory limit for user containers. The value can either be an
    integer (bytes) or a string with a 'K', 'M', 'G' or 'T' prefix.
- `MYSQL_CONTAINER_NAME`: name for docker DB container
- `MYSQL_ROOT_USERNAME`: username for DB root user
- `MYSQL_DATABASE`: competition database name in DB
- `MYSQL_DATA_VOLUME_NAME`: name for DB data volume
- `SECRETS_VOLUME_NAME`: name for Hub secrets volume
- `USE_LETSENCRYPT_CERT`: flag to use Lets Encrypt certificate (`"yes"`). For testing
    purposes, can use `openssl` to issue a self-signed certificate (`"no"`).
- `EVAL_IMAGE_NAME` : name for docker eval server image
- `EVAL_CONTAINER_NAME` : name for docker eval server container. Since there is one eval
    container, this will be the exact name.
- `EVAL_CONTAINER_PORT` : port for eval server to listen on
- `EVAL_FLASK_DEBUG` : whether eval server Flask app should be started with DEBUG flag
- `DISCOURSE_FEATURE_GROUP_NAME` : Group for new users to be added to on Discourse. This
    group will control the visibility of the feature category.
- `DISCOURSE_FEATURE_CATEGORY_NAME` : Category for new features to be posted to on
    Discourse. Posts to this category will only be visible by members of the feature group
    (above) and administrators.
- `USE_DISCOURSE`: flag to use Discourse integration (`"yes"`). If Discourse integration is
    enabled, then forum posts are created for each feature that is successfully added.

### Userlist

*Currently, this method does not allow setup of template notebooks and DB credentials. Thus,
it should be avoided entirely in favor of [User and data management](#user-and-data-management).*

Optionally, you can provide a userlist in `deploy/userlist`. Include one user per row.

- Specify normal users by their username only: `testuser`
- Specify admin users by appending an indicator: `adminuser admin`

### Jupyterhub and Jupyter Notebook

You may want to modify the default `deploy/jupyterhub_config.py` file. However, you should
know what you're doing to not break things.

## Data management

Most files are stored directly on the host machine and mounted in the Hub and User
containers:

- Experiment data: `FF_DATA_DIR/data/train` and `FF_DATA_DIR/data/test`
- Problem definitions: `FF_DATA_DIR/problems`
- Notebooks and other user-created files: `FF_DATA_DIR/users`
- Configuration files for FeatureHub and JupyterHub: `FF_DATA_DIR/config`
- Log files for Hub and eval server: `FF_DATA_DIR/log`

The MySQL database is mounted on a docker data volume:

- `db-data`

### Prediction problem format

**Data format.** All tables are CSV files with rows corresponding to examples and columns
corresponding to variables.

1. Entities table. Each row in the table corresponds to one entity to make a prediction for.
2. Target table. Each row in the table corresponds to the actual target that you were trying
   to predict. The ID is implicitly given by the index into the table, such that the *ith*
   row of the target table must contain the target for the *ith* engity.
3. Featurized entities table. Optional. A set of pre-extracted features used to initialize
   machine learning models for evaluation. Recall that when users submit features, the ML
   backend evaluates them by 1) extracting the feature values from the test data 2) building
   a model from just that feature 3) computing metrics from the trained model. If a
   featurized entities table is table, then step 2 is replaced by merging the newly
   extracted feature values with the set of existing featurized. This can be
   helpful if there are really obvious features that you don't want users to spend time
   re-implementing one-by-one, or if there are several features that dominate performance
   but that are already known, and improvements should be focused on the margins.
4. "Static" tables. There can be many of these. Metadata that doesn't change over time,
   other relational data.

A train/test split should be created, where each split contains the same set of tables but
with different cutoffs.

## User management

Users can be added or deleted using `deploy/users.py`. This utility creates user accounts on
the hub container, sets up notebooks templates, sets up authentication for each user with
the DB, and optionally sets up user accounts on the Discourse forum.

## App administration

Admins can perform administrative tasks with respect to the FeatureHub app as well as
the FeatureHub data science experiment. Admin users can manage and organize an
experiment without needing access to the host machine.

Create an admin user using `users.py add --admin=True admin_username admin_password`.

App admin

- Can log into JupyterHub via the admin web interface and add/remove users, restart/shutdown
    notebooks, and more.
- Can also create/remove users from the host machine command line using `users.py`.
- Can modify the experiment database.

Experiment admin

- Can log into JupyterHub and use the `notebooks/admin/Admin.ipynb` notebook to initialize
    experiments, restart experiments, and view features created.
- To create an experiment, the admin user must store data on the server, then execute
    Python commands to initialize the experiment and database, provide paths to the
    experiment data, and configure experiment parameters.

### Hub API client

Admins can also use a command line API client to interact with the Hub's REST API. To use
this, you must set an API key for the client to use in the `HUB_CLIENT_API_TOKEN`
environment variable. See [App Deployment](#app-deployment) above.

See the available commands:
```
hub_client.py -- --help
```

List all users:
```
hub_client.py list-users
```

Start the server of a user that already exists:
```
hub_client.py start-server username
```

## Manage app lifecycle

The available tasks can be viewed with
```
make help
```

### Restarting the server

You may want to restart the server to modify configuration of JupyterHub, update the
FeatureHub code, or some other reason.

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

Up the app.
```
make up
```

Down the app. This stops and removes the hub, user, and database containers. Note that hub
state files persist, user notebooks, and the database dump persist on the filesystem.
```
make down
```

*Optional*: Clean filesystem and containers. This stops and removes all FeatureHub
containers, if not been already done. Additionally, user notebooks and config files are
removed and data volumes are deleted. 
```
make clean
```

*Optional*: In addition to the steps taken by `make clean`, cleans images, network, in
addition to filesystem and containers.  This removes all trace of FeatureHub beside the
source repository and the experiment data directory. Built images are removed and the docker
internal network is shut down.
```
make clean_all
```

## Other topics

### Local installation

In the [Installation](#installation) section above, the FeatureHub package is built
into a Docker image. If you want to install it locally, for development and testing, there
are several additional considerations.

This is largely untested.

1. Follow the directions in above section to checkout the package and install Python 3.

2. Install required MySQL and auto-sklearn libraries and dependencies. See
     [Dockerfile-user](../deploy/Dockerfile-user) for an example on Ubuntu. See
     [auto-sklearn Intallation](http://automl.github.io/auto-sklearn/stable/installation.html)
     for details on installing auto-sklearn dependencies in your environment.

4. Install package.
    ```bash
    pip install -e src/

