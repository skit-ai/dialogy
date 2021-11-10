# Dialogy

[![Build Status](https://github.com/skit-ai/dialogy/actions/workflows/basic_test_coverage.yml/badge.svg?branch=master)](https://github.com/skit-ai/dialogy/actions/workflows/basic_test_coverage.yml)
[![Coverage Status](https://codecov.io/gh/skit-ai/dialogy/branch/master/graph/badge.svg?token=WAJ4LUTC76)](https://codecov.io/gh/skit-ai/dialogy)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/03ab1c93c9354def81de73ba04b0d94c)](https://www.codacy.com/gh/skit-ai/dialogy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Vernacular-ai/dialogy&amp;utm_campaign=Badge_Grade)
[![PyPI version](https://badge.fury.io/py/dialogy.svg)](https://badge.fury.io/py/dialogy)

Dialogy is a library for building SLU applications.
[Documentation](https://skit-ai.github.io/dialogy/)

## Installation

```shell
pip install dialogy
```

Dialogy's CLI supports building and migration of projects.

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

## Concepts

There are a few key concepts to build a machine-learning `Workflow`(s) using Dialogy.
All the effects comprising pre-processing, classification, scoring, ranking, etc are governed by `Plugin`(s).

### Workflow

A workflow has these objectives.

1. Allow interactions between different plugins.

2. Isolating plugins from each other. A plugin can't access another in the chain.

3. Storing the information till the end of the execution of plugin chain.

### Plugin

A plugin transforms data. Depending on its utility, a plugin may have phases of operation.

- Bulk transformation during training phase.

- Inference or Transformation

## Test

```shell
make test
```
