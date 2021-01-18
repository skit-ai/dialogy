# Dialogy

[![Build Status](https://travis-ci.com/Vernacular-ai/dialogy.svg?branch=master)](https://travis-ci.com/Vernacular-ai/dialogy)
[![Coverage Status](https://coveralls.io/repos/github/Vernacular-ai/dialogy/badge.svg?branch=master)](https://coveralls.io/github/Vernacular-ai/dialogy?branch=master)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/03ab1c93c9354def81de73ba04b0d94c)](https://www.codacy.com/gh/Vernacular-ai/dialogy/dashboard?utm_source=github.com&utm_medium=referral&utm_content=Vernacular-ai/dialogy&utm_campaign=Badge_Grade)

Dialogy is a battries-included 🔋 opinionated framework to build machine-learning solutions for speech applications. 

-   Plugin-based: Makes it easy to import/export components to other projects. 🔌
-   Stack-agnostic: No assumptions made on ML stack; your choice of machine learning library will not be affected by using Dialogy. 👍
-   Progressive: Minimal boilerplate writing to let you focus on your machine learning problems. 🤏

## Installation

```shell
pip install dialogy
```

## Test

```shell
make test
```

## Examples

Using `dialogy` to run a classifier on a new input.

```python
import pickle
from dialogy.workflow import Workflow
from dialogy.preprocessing import merge_asr_output


def access(workflow):
    return workflow.input


def mutate(workflow, value):
    workflow.input = value


def vectorizer(workflow):
    vectorizer = TfidfVectorizer()
    workflow.input = vectorizer.transform(workflow.input)


class TfidfMLPClfWorkflow(Workflow):
    def __init__(self):
        super(TfidfMLPClfWorkflow).__init__()
        self.model = None

    def load_model(self, model_path):
        with open(model_path, "rb") as binary:
            self.model = binary.load()

    def inference(self):
        self.output = self.model.predict(self.input)


preprocessors = [merge_asr_output(access=access, mutate=mutate), vectorizer]
workflow = TfidfMLPClfWorkflow(preprocessors=preprocessors, postprocessors=[])
output = workflow.run([[{"transcript": "hello world", "confidence": 0.97}]]) # output -> _greeting_
```

Refer to the source for [`merge_asr_output`](./dialogy/preprocessing/text/merge_asr_output.py) and [`Plugins`](./docs/plugins/README.md) to understand this example better.

## Note

-   Popular workflow sub-classes will be accepted after code-review.

## Docs

-   [Plugins](./docs/plugins/README.md)
-   [Workflow](./docs/workflow/README.md)
-   [Errors](./docs/errors/README.md) (WIP)
-   [Types](./docs/types/README.md) (WIP)
-   [Parsers](./docs/parsers/README.md) (WIP)
-   [Pre-Processors](./docs/preprocessing/README.md) (WIP)
-   [Post-Processors](./docs/postprocessing/README.md) (WIP)

## FAQs

### Training boilerplate

❌. This is not an end-to-end automated model training framework. That said, no one wants to write boilerplate code,
unfortunately, it doesn't align with the objectives of this project. Also, it is hard to accomodate for different needs 
like: 

-   library dependencies 
-   hardware support
-   Need for visualizations/reports during/after training.

Any rigidity here would lead to distractions both to maintainers and users of this project. [`Plugins`](./docs/plugins/README.md) and custom
[Workflow](./docs/workflow/README.md) are certainly welcome and can take care of recipe-based needs. 

### Common Evaluation Plans

❌. Evaluation of models is hard to standardize. if you have a fairly common need, feel free to contribute your `workflow`, `plugins`.

### Benefits

-   ✅. This project offers a conduit for an untrained model. This means once a [workflow](./dialogy/workflow/README.md) is ready you can use it anywhere:
    evaluation scripts, serving your models via an API, custom training/evaluation scripts, combining another workflow, etc. 

-   ✅. If your application needs spoken language understanding, you should find little need to write data processing functions.

-   ✅. Little to no learning curve, if you know python you know how to use this project.

## Contributions

-   Go through the docs.

-   Name your branch as "purpose/short-description". examples:
    -   "feature/hippos_can_fly"
    -   "fix/breathing_water_instead_of_fire"
    -   "docs/chapter_on_mighty_sphinx"
    -   "refactor/limbs_of_mummified_pharao"
    -   "test/my_patience"

-   Make sure tests are added are passing. Run `make test lint` at project root. Coverage is important aim for 100% unless reviewer agrees.
