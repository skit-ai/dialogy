# Dialogy

Dialogy is a battries-included 🔋 opinionated framework to build machine-learning solutions for speech applications. 

- Plugin-based: Makes it easy to import/export components to other projects. 🔌
- Stack-agnostic: No assumptions made on ML stack; your choice of machine learning library will not be affected by using Dialogy. 😏
- Progressive: Minimal boilerplate writing to let you focus on your machine learning problems. 🤏

## Installation
```shell
pip install dialogy
```

## Examples
Using `dialogy` to run a classifier on a new input.

```python
import pickle
from dialogy.workflow import Workflow
from dialogy.preprocessing import merge_asr_output


def get_utterance(workflow):
    return workflow.input


def set_input(workflow, value):
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


preprocessors = [merge_asr_output(get_utterance, set_input), vectorizer]
workflow = TfidfMLPClfWorkflow(preprocessors=preprocessors, postprocessors=[])
output = workflow.run([[{"transcript": "hello world", "confidence": 0.97}]]) # output -> _greeting_
```

## Note
- Popular workflow sub-classes will be accepted after code-review.

## Docs

- [Errors](./dialogy/errors/README.md)
- [Parsers](./dialogy/parsers/README.md)
- [Post-Processors](./dialogy/postprocessing/README.md)
- [Pre-Processors](./dialogy/preprocessing/README.md)
- [Types](./dialogy/types/README.md)
- [Workflow](./dialogy/workflow/README.md)

## FAQs

### Will Dialogy help me with model training boilerplate?
❌. This is not an end-to-end automated model training framework. That said, no one wants to write boilerplate code,
it doesn't align with the objectives of this project also it is hard to accomodate for different needs 
like: 

- library dependencies 
- hardware support
- Need for visualizations/reports during/after training.

Any rigidity here would lead to distractions both to maintainers and users of this project. Therefore we will provide **plugin support**.
Separate, isolated and lightweight libraries that just work for a recipe.

### Shouldn't evaluation be common if we are using this software?
❌. Evaluation of models is hard to standardize. if you have a fairly common need, feel free to contribute plugins.

### What are the benefits of using this project?
- ✅. This project offers a conduit for an untrained model. This means once a [workflow](./dialogy/workflow/README.md) is coded you can use it anywhere:
evaluation scripts, serving your models via an API, combining another workflow, etc. 
- ✅. If your application needs spoken language understanding, you should find little need to write data processing functions.
- ✅. Little to no learning curve, if you know python you know how to use this project.

## Future
- [ ] Duckling parsers and support.
- [ ] Cookiecutter project installation.
- [ ] Conversation driven development.

