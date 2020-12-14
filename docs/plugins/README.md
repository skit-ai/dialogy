# Plugins

A plugin is a `Callable` that requires a [`Workflow`](./docs/workflow/README.md) instance as its only argument. 
This is standard for many functions within this project to help its extensibility. 


## Plugins are functions

Let's look at a few example plugins:

### Naive plugin

```python
from dialogy.workflow import Workflow


def barely_useful_tokenizer_plugin(workflow: Workflow):
    """
    Separate words in a sentence by " ".
    """
    # assuming consumers would have `workflow.input` as `str`.
    text = workflow.input
    if not isinstance(text, str):
        raise TypeError(f"Expected str found {type(text)}.")
    if not text:
        raise ValueError(f"Expected str of non-zero length.")

    # assuming the previously held value is of no relevance.
    workflow.input = text.split(" ")
```

This plugin is a pre-processing function that splits each word in a given sentence by space, and replaces the value held by the current `workflow.input`.
The successor to this function would receive a `List[str]` as `workflow.input`.


### A better plugin
Let's try to create a plugin to split on [`regex`](https://docs.python.org/3/library/re.html) patterns. 💡 

```python
import re
from dialogy.workflow import Workflow


def better_tokenizer_plugin(pattern: str = r" ", maxsplit: int = 0, flags = re.I | re.U):
    # Always compile strings before using them in loops.
    pattern = re.compile(pattern, maxsplit=maxsplit, flags=flags)
    def plugin(workflow: Workflow):
        """
        Split a sentence by given regex pattern.
        """
        # assuming consumers would have `workflow.input` as `str`.
        text = workflow.input
        if not isinstance(text, str):
            raise TypeError(f"Expected str found {type(text)}.")
        if not text:
            raise ValueError(f"Expected str of non-zero length.")

        # assuming the previously held value is of no relevance.
        workflow.input = pattern.split(text)
    return inner
```

This plugin offers more utility because we can use the [`re`](https://docs.python.org/3/library/re.html) library to tokenize inputs. This plugin is still not ready for general use. The assumptions made by this plugin has a tendency to hurt its utility. The author assumes (as can be seen in the comments) that:

> assuming consumers would have `workflow.input` as `str`.

> assuming the previously held value is of no relevance.

These assumptions may not work for everyone, so how do we let consumers have a choice? 🤔

### Final form

```python
import re
from typing import Callable
from dialogy.workflow import Workflow


def user_friendly_better_tokenizer_plugin(
    pattern: str = r" ", 
    maxsplit: int = 0, 
    flags = re.I | re.U, 
    access: Callable = None, 
    mutate: Callable = None):

    # Always compile strings before using them in loops.
    pattern = re.compile(pattern, maxsplit=maxsplit, flags=flags)

    def plugin(workflow: Workflow):
        text = access(workflow)

        if not isinstance(text, str):
            raise TypeError(f"Expected str found {type(text)}.")
        if not text:
            raise ValueError(f"Expected str of non-zero length.")

        tokenized_text = pattern.split(text)
        mutate(workflow, tokenized_text)
    return inner
```

Now we can easily interact with the plugin adequately. An accessor function `access`, allows us to specify the contract to 
receive inputs from her workflow. Likewise, a mutator function `mutate`, helps modifying the state of our `workflow`.
The plugin is only responsible for access, operations and dispatch on data.

## Plugins are stateful too!

There is yet another challenge. We saw plugins that are just functions with some convention, but what if a plugin requires a state? 

Say a consumers want to encode sentences to vectors using [`sentence-transformers`](https://www.sbert.net/)? A function would load that model for each iteration, and that's no good. `Dialogy` also provides an [abstact class](https://docs.python.org/3/library/abc.html), `Plugin` that can be used for such cases.

```python
from typing import Callable
from dialogy.workflow import Workflow
from dialogy.plugins import Plugin


class Sentence2VecPlugin(Plugin):
    def __init__(self):
        super(Sentence2Vec).__init__()
        self.model = None

    def load(self, model_path=None):
        with open(model_path, "rb") as binary:
            self.model = binary.load()
        
    def exec(self, access: Callable = None, mutate: Callable = None):
        def plugin(workflow):
            sentence = access(workflow)

            if not isinstance(access, Callable):
                raise TypeError(f"Expected access to be a Callable got {type(access)} instead.")
            if not isinstance(mutate, Callable): 
                raise TypeError(f"Expected mutate to be a Callable got {type(access)} instead.")

            if not isinstance(text, str):
                raise TypeError(f"Expected str found {type(text)}.")
            if not text:
                raise ValueError(f"Expected str of non-zero length.")

            vectorized_sentence = self.model.encode([sentence])
            mutate(workflow, vectorized_sentence)
        return plugin
```

## Summary
We will summarize a few key points for creating plugins:
- Don't interact with the workflow directly, use functions to access and mutate.
- The convention for workflow access is `access(workflow)`.
- The convention for workflow modification is `mutate(workflow, value)`.
- We can easily access multiple parts of a workflow by expecting `access` functions to return `Tuple`, `List` or `Dict`.
- Likewise, we can easily modify multiple parts of a workflow by expecting `mutate` functions to accept `Tuple`, `List` or `Dict` as values.
- Plugin authors must provide good documentation for `access` and `mutate` functions that work with their plugin.
- **Plugin names must end with Plugin for classes and _plugin for functions.**
