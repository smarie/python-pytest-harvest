# python-pytest-harvest

*Store data created during your `pytest` tests execution, and retrieve it at the end of the session, e.g. for applicative benchmarking purposes.*

[![Python versions](https://img.shields.io/pypi/pyversions/pytest-harvest.svg)](https://pypi.python.org/pypi/pytest-harvest/) [![Build Status](https://travis-ci.org/smarie/python-pytest-harvest.svg?branch=master)](https://travis-ci.org/smarie/python-pytest-harvest) [![Tests Status](https://smarie.github.io/python-pytest-harvest/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-pytest-harvest/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-pytest-harvest/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-pytest-harvest)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-pytest-harvest/) [![PyPI](https://img.shields.io/pypi/v/pytest-harvest.svg)](https://pypi.python.org/pypi/pytest-harvest/) [![Downloads](https://pepy.tech/badge/pytest-harvest)](https://pepy.tech/project/pytest-harvest) [![Downloads per week](https://pepy.tech/badge/pytest-harvest/week)](https://pepy.tech/project/pytest-harvest) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-pytest-harvest.svg)](https://github.com/smarie/python-pytest-harvest/stargazers)


**This is the readme for developers.** The documentation for users is available here: [https://smarie.github.io/python-pytest-harvest/](https://smarie.github.io/python-pytest-harvest/)

## Want to contribute ?

Contributions are welcome ! Simply fork this project on github, commit your contributions, and create pull requests.

Here is a non-exhaustive list of interesting open topics: [https://github.com/smarie/python-pytest-harvest/issues](https://github.com/smarie/python-pytest-harvest/issues)

## Running the tests

This project uses `pytest`.

```bash
pytest -v pytest_harvest/tests/
```

You may need to install requirements for setup beforehand, using 

```bash
pip install -r ci_tools/requirements-pip.txt
```

## Packaging

This project uses `setuptools_scm` to synchronise the version number. Therefore the following command should be used for development snapshots as well as official releases: 

```bash
python setup.py egg_info bdist_wheel rotate -m.whl -k3
```

You may need to install requirements for setup beforehand, using 

```bash
pip install -r ci_tools/requirements-pip.txt
```

## Generating the documentation page

This project uses `mkdocs` to generate its documentation page. Therefore building a local copy of the doc page may be done using:

```bash
mkdocs build -f docs/mkdocs.yml
```

You may need to install requirements for doc beforehand, using 

```bash
pip install -r ci_tools/requirements-pip.txt
```

## Generating the test reports

The following commands generate the html test report and the associated badge. 

```bash
pytest --junitxml=junit.xml -v pytest_harvest/tests/
ant -f ci_tools/generate-junit-html.xml
python ci_tools/generate-junit-badge.py
```

### PyPI Releasing memo

This project is now automatically deployed to PyPI when a tag is created. Anyway, for manual deployment we can use:

```bash
twine upload dist/* -r pypitest
twine upload dist/*
```

### Merging pull requests with edits - memo

Ax explained in github ('get commandline instructions'):

```bash
git checkout -b <git_name>-<feature_branch> master
git pull https://github.com/<git_name>/python-pytest-harvest.git <feature_branch> --no-commit --ff-only
```

if the second step does not work, do a normal auto-merge (do not use **rebase**!):

```bash
git pull https://github.com/<git_name>/python-pytest-harvest.git <feature_branch> --no-commit
```

Finally review the changes, possibly perform some modifications, and commit.
