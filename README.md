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
