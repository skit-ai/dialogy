# Dialogy 🔹

Dialogy is a battries-included 🔋 opinionated framework to build machine-learning solutions for speech applications. 

- 🔌 Plugin-based: Makes it easy to import/export components to other projects. 
- 😏 Stack-agnostic: No assumptions made on ML stack; your choice of machine learning library will not be affected by using Dialogy. 
- 🤏 Progressive: Minimal boilerplate writing to let you focus on your machine learning problems. 

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
    workflow.input = vectorizer.transform(workflow.input[-1])


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
