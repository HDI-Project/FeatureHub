# Building documentation

FeatureHub uses Sphinx to build documentation.

- Install FeatureHub Python package dependencies, as package is imported to extract
    docstrings for API reference.
- Install additional dependences
    - pandoc: See installation information for your platform at http://pandoc.org/installing.html.
- Install additional Python packages for building documentation
    ```
    pip install -r ./requirements.txt
    ```

Then, to build html documentation, run
```
make html
```

You can also run a devserver at
```
make htmlserver
```

Make sure to kill the server when you are done
```
make stopserver
```
