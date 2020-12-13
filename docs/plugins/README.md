# Plugins

A plugin is a callable that requires a workflow instance as its only argument. 
This is standard for many functions within this project to help its extensibility. Let's look at a few example plugins:

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

Let's try to create a plugin where the delimiter is an argument. 🤔 

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

This new plugin offers more utility because the consumer can now use the regular expression library to tokenize their inputs. There are still problems.
The assumptions made by these plugins have a tendency to break their utility. The author assumes (as can be seen in the comments) that:

> # assuming consumers would have `workflow.input` as `str`.

> # assuming the previously held value is of no relevance.

These assumptions may not work for everyone, so how do we let consumers have a choice?

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

        mutate(workflow, text)
    return inner
```

Now consumers can easily interact with the plugin adequately, an accessor function `access` allows a consumer to specify 
how to receive inputs from her workflow.
