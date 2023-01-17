# Dialogy

[![Build Status](https://github.com/skit-ai/dialogy/actions/workflows/basic_test_coverage.yml/badge.svg?branch=master)](https://github.com/skit-ai/dialogy/actions/workflows/basic_test_coverage.yml)
[![Coverage Status](https://codecov.io/gh/skit-ai/dialogy/branch/master/graph/badge.svg?token=WAJ4LUTC76)](https://codecov.io/gh/skit-ai/dialogy)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/03ab1c93c9354def81de73ba04b0d94c)](https://www.codacy.com/gh/skit-ai/dialogy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Vernacular-ai/dialogy&amp;utm_campaign=Badge_Grade)
[![PyPI version](https://badge.fury.io/py/dialogy.svg)](https://badge.fury.io/py/dialogy)

Dialogy is a library for building and managing SLU applications.
[Documentation](https://skit-ai.github.io/dialogy/)

## Installation

```shell
pip install dialogy
```


Dialogy's CLI supports building and migration of projects. Migration is hard because a few modules need a forced update but a few others
should be retained by the developer. The lack of this expression makes it hard to migrate smoothly. Building new projects should be fairly simple.

```txt
dialogy -h
usage: dialogy [-h] {create,update,train} ...

positional arguments:
  {create,update,train}
                        Dialogy project utilities.
    create              Create a new project.
    update              Migrate an existing project to the latest template version.
    train               Train a workflow.

optional arguments:
  -h, --help            show this help message and exit
```

## Project Creation

```txt
dialogy create -h
usage: dialogy create [-h] [--template TEMPLATE] [--dry-run] [--namespace NAMESPACE] [--master] project

positional arguments:
  project               A directory with this name will be created at the root of command invocation.

optional arguments:
  -h, --help            show this help message and exit
  --template TEMPLATE
  --dry-run             Make no change to the directory structure.
  --namespace NAMESPACE
                        The github/gitlab user or organization name where the template project lies.
  --master              Download the template's master branch (HEAD) instead of the latest tag.
```

## Building

To build SLU pipelines using Dialogy, you would need to understand the building blocks.

1. Input
2. Output
3. Plugin
4. Workflow 

### Input

A class that contains initial values / placeholders for the pipeline.

### Output

A class that contains the results / placeholders for the pipeline.

### Plugin

- A Plugin is an abstract class with an abstract method `def utility(i: Input, o: Output) -> Any`.
- Initialize your class with artifact paths, reading files, loading models, etc. 
- At runtime we call the `utility` method to get the results.

### Workflow

- A workflow is a map over all the plugins in a sequence, as desired by the pipeline creator. 
- The workflow iterates over each plugin, calls its `utility` method.
- Each plugin sets the value within the workflow automatically.

## Test

```shell
make test
```

## Contributors

Clone the repository. We use [poetry](https://python-poetry.org/) to setup dependencies.

```shell
git clone git@github.com:skit-ai/dialogy.git
cd dialogy
# Activate your virtualenv, you can also let poetry take care of it.
poetry install
make test
```
Ensure tests are passing before you start working on your PRs.

[read here](https://github.com/skit-ai/dialogy/blob/master/CONTRIBUTING.md)

### Release mechanisms

We follow [semantic versioning](https://semver.org/) to name new versions of the library.
All new versions are hosted on PyPI and automatically pushed to PyPI 
once a new tag is pushed to git. For e.g. if you want to release a new version `0.9.27` on PyPI, 
checkout `master` branch, create a new tag and push the tag to github:
```commandline
git checkout master
git pull
git tag -a '0.9.27' -m 'new example release'
git push -u origin 0.9.27
```

**Note**: We are introducing major breaking changes to the library. As we go 
through this transition and have the new changes adopted across all client code bases, we will need
to support both the old API and new API of the library. For that reason, releases for the old API
will happen through the `0.9.x` branch and will result in 
new patch versions of the same minor version, for e.g. `0.9.30`.

The new API will live on `master` and all changes built on top of new API 
should be released from `master` with minor version `0.10`, for e.g. `0.10.2`.