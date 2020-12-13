# Plugins

A plugin is a callable that requires a workflow instance as its only argument. 
This is standard for many functions within this project to help its extensibility. 


## Plugins are functions

### Naive plugin
Let's look at a few example plugins:

```python
from dialogy.workflow import Workflow


def barely_useful_tokenizer(workflow: Workflow):
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

This plugin is a pre-processing function that splits each word in a given sentence and replaces the value held by the current input.
The successor to this function would receive a `List[str]` as `workflow.input`.


### A better plugin
Let's try to create a plugin where the delimiter is an argument. 💡 

```python
import re
from dialogy.workflow import Workflow


def better_tokenizer(pattern: str = r" ", maxsplit: int = 0, flags = re.I | re.U):
    # Always compile strings before using them in loops.
    pattern = re.compile(pattern, maxsplit=maxsplit, flags=flags)
    def inner(workflow: Workflow):
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

This new plugin offers more utility because the consumer can now use the regular expression library to tokenize their inputs. There are still problems with this plugin. The assumptions made by these plugins have a tendency to break their utility. The author assumes (as can be seen in the comments) that:

> assuming consumers would have `workflow.input` as `str`.

> assuming the previously held value is of no relevance.

These assumptions may not work for everyone, so how do we let consumers have a choice? 🤔

### Final form

```python
import re
from typing import Callable
from dialogy.workflow import Workflow


def user_friendly_better_tokenizer(
    pattern: str = r" ", 
    maxsplit: int = 0, 
    flags = re.I | re.U, 
    access: Callable = None, 
    mutate: Callable = None):

    # Always compile strings before using them in loops.
    pattern = re.compile(pattern, maxsplit=maxsplit, flags=flags)

    def inner(workflow: Workflow):
        text = access(workflow)

        if not isinstance(text, str):
            raise TypeError(f"Expected str found {type(text)}.")
        if not text:
            raise ValueError(f"Expected str of non-zero length.")

        tokenized_text = pattern.split(text)
        mutate(workflow, tokenized_text)
    return inner
```

Now consumers can easily interact with the plugin adequately. An accessor function `access`, allows a consumer to specify 
how to receive inputs from her workflow. Meanwhile a mutator function `mutate`, helps modifying the `workflow` only as per the consumer's desire.
The plugin only offers a value.

## Plugins are classes too!

There is yet another challenge. We saw functional plugins but what if a plugin requires a state? say a consumers want to encode sentences to vectors using
sentence_embeddings? A function only interface would make that difficult. `Dialogy` also provides a `Plugin` class ([abstact](https://docs.python.org/3/library/abc.html)) that can be used for such cases.

```python
from typing import Callable
from dialogy.workflow import Workflow
from dialogy.plugins import Plugin

class Sentence2Vec(Plugin):
    def __init__(self):
        super(Sentence2Vec, self).__init__()
        self.model = None

    def load(model_path=None):
        with open(model_path, "rb") as binary:
            self.model = binary.load()
        
    def exec(workflow, access: Callable = None, mutate: Callable = None):
        sentence = access(workflow)

        if not isinstance(access, Callable):
            raise TypeError(f"Expected access to be a Callable got {type(access)} instead.")
        if not isinstance(mutate, Callable): 
            raise TypeError(f"Expected mutate to be a Callable got {type(access)} instead.")

        if not isinstance(text, str):
            raise TypeError(f"Expected str found {type(text)}.")
        if not text:
            raise ValueError(f"Expected str of non-zero length.")

        vectorized_sentence = self.model(sentence)
        mutate(workflow, vectorized_sentence)
```

## Summary
We will summarize a few key points for creating plugins:
- Don't directly interact with the workflow directly.
- The convention for workflow access is `access(workflow)`.
- The convention for workflow modification is `mutate(workflow, value)`.
- We can easily access multiple parts of a workflow by expecting `access` functions to return `Tuple`, `List` or `Dict`.
- Likewise, we can easily modify multiple parts of a workflow by expecting `mutate` functions to accept `Tuple`, `List` or `Dict` as values.
- Plugin authors must provide good documentation for `access` and `mutate` functions that work with their plugin.
