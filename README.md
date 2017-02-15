# FeatureFactory

*FeatureFactory* is a web application built on top of JupyterHub and an accompanying Python
package that together facilitate collaborative data science efforts as well as data collection
experiments on those efforts.

The FeatureFactory Python package is used to administer a data science collaboration. It
allows users to "register" features in a database backend and discover features written by
other users. These features are automatically scored by the system so that users can see
realtime feedback on the quality of their features.

The FeatureFactory app includes a JupyterHub server, containerized Jupyter notebooks for
each user with the FeatureFactory package installed, a database backend to store the
features, and data- and user-management tools.

## Deployment

The FeatureFactory app can be deployed quite easily, thanks to docker and docker-compose.

1. Install [Docker Engine](https://docs.docker.com/engine/installation/) and [Docker Compose](https://docs.docker.com/compose/install/) on your system.

2. Download the FeatureFactory repository.
    ```
    git clone https://github.com/HDI-Project/FeatureFactory.git
    ```

3. Modify app configuration variables in `deploy/.env`.

4. *Optional*: Populate a userlist, if desired, in `deploy/userlist`.

5. Build the necessary docker images.
    ```
    cd deploy/
    make build
    ```

6. Launch the app.
    ```
    make up
    ```

The available tasks can be viewed with
```
make help
```

### Restarting the server

You may want to restart the server to modify configuration of JupyterHub, update the
FeatureFactory code, or some other reason.

Stop the app. This stops and removes the hub, user, and database containers. Note that hub
state files persist, user notebooks, and the database dump persist on the filesystem.
```
cd deploy/
make down
```

*Optional*: Clean filesystem and containers. This stops and removes all FeatureFactory
containers, if not been already done. Additionally, user notebooks and config files are
removed. Note that this *does not clear the database*, which may then retain information
relating to non-existent users and expect user credentials that have been deleted.
```
make clean
```

*Optional*: Clean images, network, and volumes, in addition to filesystem and containers.
This removes all trace of FeatureFactory beside the source repository and the experiment
data directory. Built images are removed, the docker internal network is shut down, and the
database volume is removed.
```
make clean_all
```

## App administration

Admins can perform administrative tasks with respect to the FeatureFactory app as well as
the FeatureFactory data science experiment. Admin users can manage and organize an
experiment without needing access to the host machine.

First, create an admin user using `add_user.sh -a admin_username admin_password`.

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

## User and data management

Users can be added or deleted using `deploy/add_user.sh` and `deploy/delete_user.sh`.

Most files are stored directly on the host machine:
- Experiment data: `FF_DATA_DIR/data`
- Notebooks and other user-created files: `FF_DATA_DIR/users`
- Configuration files for FeatureFactory and JupyterHub: `FF_DATA_DIR/config`

The MySQL database is mounted on a docker data container:
- `featurefactory_db-data`

## Manual package installation (advanced)

You can manually install the package, separate from the JupyterHub deployment. Indeed, these
exact steps are part of the user notebook server Dockerfile.

Install dependencies
```
pip install -r requirements.txt
```

The package needs to be installed from within `src` folder using `setup.py`.

```
cd src
python setup.py install
```

### Usage

Once it the package is installed, the `orm.admin.Commands` class can be used to initiate
the DB environment and register the problems.
The Jupyter Notebooks found in `notebooks/admin` folder contain some usage examples.

After the environment is set-up, a Jupyter notebook instance needs to be started from within
the problem folder, inside the `notebooks` directory.
