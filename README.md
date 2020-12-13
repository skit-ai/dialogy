# Dialogy

Dialogy is a battries-included 🔋 opinionated framework to build machine-learning solutions for speech applications. 

- Plugin-based: Makes it easy to import/export components to other projects. 🔌
- Stack-agnostic: No assumptions made on ML stack; your choice of machine learning library will not be affected by using Dialogy. 😏
- Progressive: Minimal boilerplate writing to let you focus on your machine learning problems. 🤏

## Installation
```shell
pip install dialogy
```

## Test
```
make
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
        super(TfidfMLPClfWorkflow, self).__init__()
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
Refer to the source for [merge_asr_output](./dialogy/preprocessing/text/merge_asr_output.py) and [Plugins](./docs/plugins/README.md) to understand this example better.

## Note
- Popular workflow sub-classes will be accepted after code-review.

## Docs

- [Errors](./docs/errors/README.md)
- [Types](./docs/types/README.md)
- [Parsers](./docs/parsers/README.md)
- [Pre-Processors](./docs/preprocessing/README.md)
- [Post-Processors](./docs/postprocessing/README.md)
- [Workflow](./docs/workflow/README.md)
- [Plugins](./docs/plugins/README.md)

## FAQs

### Will Dialogy help me with model training boilerplate?
❌. This is not an end-to-end automated model training framework. That said, no one wants to write boilerplate code,
unfortunately, it doesn't align with the objectives of this project also it is hard to accomodate for different needs 
like: 

- library dependencies 
- hardware support
- Need for visualizations/reports during/after training.

Any rigidity here would lead to distractions both to maintainers and users of this project. Therefore we will provide **plugin support**.
Separate, isolated and lightweight libraries that just work for a recipe.

### Shouldn't evaluation be common if we are using this software?
❌. Evaluation of models is hard to standardize. if you have a fairly common need, feel free to contribute your `workflow` or `plugins`.

### What are the benefits of using this project?
- ✅. This project offers a conduit for an untrained model. This means once a [workflow](./dialogy/workflow/README.md) is coded you can use it anywhere:
evaluation scripts, serving your models via an API, combining another workflow, etc. 
- ✅. If your application needs spoken language understanding, you should find little need to write data processing functions.
- ✅. Little to no learning curve, if you know python you know how to use this project.

## Contrib
- Go through the docs.
- Name your branch as "purpose/short-description". examples:
    - "feature/hippos_can_fly"
    - "fix/breathing_water_instead_of_fire"
    - "docs/chapter_on_mighty_sphinx"
    - "refactor/limbs_of_mummified_pharao"
    - "test/my_patience"
- Make sure tests are added are passing. Run `make` at project root. Coverage is important aim for 100% unless reviewer agrees.

## Future
- [ ] Duckling parsers and support.
- [ ] Cookiecutter project installation.
- [ ] Conversation driven development.
