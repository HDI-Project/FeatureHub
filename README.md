# FeatureHub

[![](https://img.shields.io/badge/docs-latest-blue.svg)](https://HDI-Project.github.io/FeatureHub)

*FeatureHub* is a web application built on top of JupyterHub and an accompanying Python
package that together facilitate collaborative data science efforts as well as data collection
experiments on those efforts.

The FeatureHub Python package is used to administer a data science collaboration. It
allows users to "register" features in a database backend and discover features written by
other users. These features are automatically scored by the system so that users can see
realtime feedback on the quality of their features.

The FeatureHub app includes a JupyterHub server, containerized Jupyter notebooks for
each user with the FeatureHub package installed, a database backend to store the
features, and data- and user-management tools.

## Citing FeatureHub

Please consider referencing the following paper:

> M. J. Smith, R. Wedge, and K. Veeramachaneni, ["FeatureHub: Towards collaborative data
> science,"](https://www.micahsmith.com/files/featurehub-smith.pdf) in Data Science and
> Advanced Analytics (DSAA), 2017. *IEEE International Conference on.* IEEE, 2017, pp. 1-11.
