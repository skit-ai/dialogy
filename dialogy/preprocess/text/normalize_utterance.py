"""
This module was created in response to: https://github.com/Vernacular-ai/dialogy/issues/9
we will ship functions to assist normalization of ASR output, we will refer to these as Utterances.
"""
from functools import partial
from typing import Any, Callable, Dict, List

from dialogy import constants as const


def dict_get(prop: str, obj: Dict[str, Any]) -> Any:
    """
    Get value of prop within obj.

    Args:
        prop (str): A key within a dict.
        obj (Dict[str, Any]): Any dict.

    Returns:
        Any
    """
    return obj[prop]


def is_list(input_: Any) -> bool:
    """
    Check type of `input_`

    Args:
        input_ (Any): Any arbitrary input.

    Returns:
        bool: True if input_ is list.
    """
    return isinstance(input_, list)


def is_each_element(
    type_: type, input_: List[Any], transform: Callable[[Any], Any] = lambda x: x
) -> bool:
    """
    Check if each element in a list is of a given type.

    Args:
        type_ (type): Expected type for each element.
        input_ (List[Any]): Arbitrary list.
        transform (Callable[[Any], Any], optional): We may apply some transforms to
            each element before making these checks. This is to check if a certain key
            in a Dict matches the expected type. In case this is not needed,
            leave the argument unset and an identity transform is applied. Defaults to lambdax:x.

    Returns:
        bool: True if each element in input matches the type.
    """
    return all(isinstance(transform(item), type_) for item in input_)


def is_utterance(maybe_utterance: Any, key: str = const.TRANSCRIPT) -> bool:
    """
    Check input to be of `List[List[Dict]]`.

    ```json
    [[{"transcript": "hi"}]]
    ```

    Args:
        maybe_utterance (Any): Arbitrary type input.
        key (str, optional): The key within which transcription string resides.
            Defaults to const.TRANSCRIPT.

    Returns:
        bool

    Raises:
        KeyError
        TypeError
    """
    dict_get_key = partial(dict_get, key)
    try:
        return all(
            is_each_element(str, alternatives, transform=dict_get_key)
            for alternatives in maybe_utterance
        )
    except KeyError:
        return False
    except TypeError:
        return False


def is_unsqueezed_utterance(maybe_utterance: Any, key: str = const.TRANSCRIPT) -> bool:
    """
    Check input to be of `List[Dict]`.

    Args:
        maybe_utterance (Any): Arbitrary type input.
        key (str, optional): The key within which transcription string resides.
            Defaults to const.TRANSCRIPT.

    Returns:
        bool

    Raises:
        KeyError
        TypeError
    """
    dict_get_key = partial(dict_get, key)
    try:
        return is_each_element(str, maybe_utterance, transform=dict_get_key)
    except KeyError:
        return False
    except TypeError:
        return False


def is_list_of_string(maybe_utterance: Any) -> bool:
    """
    Check input to be of `List[str]`.

    Args:
        maybe_utterance (Any): Arbitrary type input.

    Returns:
        bool

    Raises:
        KeyError
        TypeError
    """
    try:
        return is_each_element(str, maybe_utterance)
    except TypeError:
        return False


def is_string(maybe_utterance: Any) -> bool:
    """
    Check input to be of `str`.

    Args:
        maybe_utterance (Any): Arbitrary type input.

    Returns:
        bool
    """
    return isinstance(maybe_utterance, str)


def normalize(maybe_utterance: Any, key: str = const.TRANSCRIPT) -> List[str]:
    """
    Adapt various non-standard ASR alternative forms.

    The output will be a list of strings since models will expect that.

    expected inputs:
    ```json
    [[{"transcript": "hi"}]]
    ```

    ```json
    [{"transcript": "I wanted to know umm hello?"}]
    ```

    ```json
    ["I wanted to know umm hello?"]
    ```

    ```json
    "I wanted to know umm hello?"
    ```

    Args:
        maybe_utterance (Any): Non-standard input types.

    Returns:
        List[str]

    Raises:
        TypeError
    """
    if is_utterance(maybe_utterance):
        return [
            alternative[key]
            for alternatives in maybe_utterance
            for alternative in alternatives
        ]

    if is_unsqueezed_utterance(maybe_utterance):
        return [alternative[key] for alternative in maybe_utterance]

    if is_list(maybe_utterance) and is_list_of_string(maybe_utterance):
        return maybe_utterance

    if is_string(maybe_utterance):
        return [maybe_utterance]

    else:
        raise TypeError(
            f"The input {maybe_utterance} does not belong to any of the expected types:"
            " List[List[Dict[str, Any]]], List[Dict[str, Any]], List[str] or str."
        )
