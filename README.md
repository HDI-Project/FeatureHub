<p align="left">
<img width=15% src="https://dai.lids.mit.edu/wp-content/uploads/2018/06/Logo_DAI_highres.png" alt=“SDV” />
<i>An open source project from Data to AI Lab at MIT.</i>
</p>



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

Please consider referencing our [paper about FeatureHub](https://www.micahsmith.com/files/featurehub-smith.pdf):

```
@inproceedings{smith2017featurehub,
  title={FeatureHub: Towards collaborative data science},
  author={Smith, Micah J and Wedge, Roy and Veeramachaneni, Kalyan},
  booktitle={2017 IEEE International Conference on Data Science and Advanced Analytics (DSAA)},
  pages={590--600},
  year={2017},
  organization={IEEE}
}
```
