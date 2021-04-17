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

    This simple function exists to facilitate a partial function defined :ref:`here<is_utterance>`.

    :param prop: A property within a :code:`dict`.
    :type prop: str
    :param obj: A :code:`dict`.
    :type obj: Dict[str, Any]
    :return: Value of a property within a :code:`dict`.
    :rtype: Any
    """
    return obj[prop]


def is_list(input_: Any) -> bool:
    """
    Check type of :code:`input`

    :param input_: Any arbitrary input
    :type input_: Any
    :return: True if :code:`input` is a :code:`list` else False
    :rtype: True
    """
    return isinstance(input_, list)


def is_each_element(
    type_: type, input_: List[Any], transform: Callable[[Any], Any] = lambda x: x
) -> bool:
    """
    Check if each element in a list is of a given type.

    .. ipython:: python

        from dialogy.preprocess.text.normalize_utterance import is_each_element

        is_each_element(str, ["this", "returns", "False", "cuz:", False])
        is_each_element(str, ["this", "returns", "True", "cuz:", "all", "str"])

    :param type_: Expected :code:`Type` of each element in the :code:`input_` which is a :code:`list`.
    :type type_: Type
    :param input_: A :code:`list`.
    :type input_: List[Any]
    :param transform: We may apply some transforms to
        each element before making these checks. This is to check if a certain key
        in a Dict matches the expected type. In case this is not needed,
        leave the argument unset and an identity transform is applied. Defaults to lambda x:x.
    :type transform: Callable[[Any], Any]
    :return: Checks each element in a list to match :code:`type_`, if any element fails the check,
        this returns False, else True.
    :rtype: bool
    """
    return all(isinstance(transform(item), type_) for item in input_)


def is_utterance(maybe_utterance: Any, key: str = const.TRANSCRIPT) -> bool:
    """
    .. _is_utterance:

    Check input to be of `List[List[Dict]]`.


    .. code-block: json

        [[{"transcript": "hi"}]]


    .. ipython:: python

        from dialogy.preprocess.text.normalize_utterance import is_utterance

        # 1. :code:`List[List[Dict[str, str]]]`
        is_utterance([[{"transcript": "this"}, {"transcript": "works"}]])

        # 2. key is configurable
        is_utterance([[{"text": "this"}, {"text": "works"}]], key="text")

        # 3. Hope for everything else... you have a mastercard.
        # Or use this lib, works just fine 🍷.
        is_utterance([{"transcript": "this"}, {"transcript": "doesn't"}, {"transcript": "work"}])

    :param maybe_utterance: Arbitrary input.
    :type maybe_utterance: Any
    :param key: The key within which transcription string resides.
            Defaults to :code:`const.TRANSCRIPT`.
    :type key: str
    :return: True if the inputs is :code:`List[List[Dict[str, str]]]`, else False.
    :rtype: bool
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

    .. ipython:: python

        from dialogy.preprocess.text.normalize_utterance import is_unsqueezed_utterance

        # 1. This fails
        is_unsqueezed_utterance([[{"transcript": "this"}, {"transcript": "works"}]])

        # 2. key is configurable
        is_unsqueezed_utterance([{"text": "this"}, {"text": "works"}], key="text")

    :param maybe_utterance: Arbitrary type input.
    :type maybe_utterance: Any
    :param key: The key within which transcription string resides.
    :type key: str, Defaults to const.TRANSCRIPT.
    :return: True, if the input is of type :code:`List[Dict[str, Any]]` else False.
    :rtype: bool
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

    .. ipython:: python

        from dialogy.preprocess.text.normalize_utterance import is_list_of_string
        is_list_of_string(["this", "works"])

    :param maybe_utterance: Arbitrary input.
    :type maybe_utterance: Any
    :return: True if :code:`maybe_utterance` is a :code:`str`.
    :rtype: bool
    """
    try:
        return is_each_element(str, maybe_utterance)
    except TypeError:
        return False


def is_string(maybe_utterance: Any) -> bool:
    """
    Check input's type is `str`.

    :param maybe_utterance: Arbitrary type input.
    :type maybe_utterance: Any
    :return: True if :code:`maybe_utterance` is a :code:`str`, else False.
    :rtype: bool
    """
    return isinstance(maybe_utterance, str)


def normalize(maybe_utterance: Any, key: str = const.TRANSCRIPT) -> List[str]:
    """
    Adapt various non-standard ASR alternative forms.

    The output will be a list of strings since models will expect that.


    .. ipython:: python

        from dialogy.preprocess import normalize

        normalize([[{"transcript": "hi"}]])
        normalize([[{"transcript": "hello"}], [{"transcript": "world"}]])
        normalize([{"transcript": "I wanted to know umm hello?"}])
        normalize(["I wanted to know umm hello?"])
        normalize("I wanted to know umm hello?")


    :param maybe_utterance: Arbitrary input.
    :type maybe_utterance: Any
    :param key: A string to be looked into :code:`List[List[Dict[str, str]]]`, :code:`List[Dict[str, str]]` type inputs.
    :type key: str
    :return: A flattened list of strings parsed from various formats.
    :rtype: List[str]
    :raises:
        TypeError: If :code:`maybe_utterance` is none of the expected types.
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
