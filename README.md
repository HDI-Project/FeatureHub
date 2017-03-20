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
