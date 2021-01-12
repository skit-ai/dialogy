import operator as op
from datetime import datetime
from functools import reduce
from typing import List, Dict, Any, Tuple, Union

# TODO: This can be better
# NOTE: yes ☝

def greater_than_today(
    utt_value: Dict[str, Any], ref_time: datetime, limit: int = 100
) -> bool:
    """[summary]

    Args:
        utt_value ([type]): [description]
        ref_time (datetime): [description]
        limit (int, optional): [description]. Defaults to 100.

    Returns:
        bool: [description]
    """
    if isinstance(utt_value["value"], Dict):
        if "from" in utt_value["value"]:
            utt_time = utt_value["value"]["from"]
        else:
            return True
    else:
        utt_time = utt_value["value"]
    if utt_time.date() == ref_time.date() and utt_value["grain"] == "day":
        return True
    if not limit:
        return utt_time > ref_time
    else:
        return utt_time > ref_time and abs(utt_time - ref_time).days <= limit


def greater_than(utt_value: Dict[str, Any], ref_time: datetime) -> bool:
    """[summary]

    Args:
        utt_value ([type]): [description]
        ref_time (datetime): [description]

    Returns:
        bool: [description]
    """
    if isinstance(utt_value["value"], Dict):
        if "from" in utt_value["value"]:
            utt_time = utt_value["value"]["from"]
        else:
            return True
    else:
        utt_time = utt_value["value"]
    return utt_time > ref_time


def greater_than_eq(utt_value: Dict[str, Any], ref_time: datetime) -> bool:
    """[summary]

    Args:
        utt_value ([type]): [description]
        ref_time (datetime): [description]

    Returns:
        bool: [description]
    """
    if isinstance(utt_value["value"], Dict):
        if "from" in utt_value["value"]:
            utt_time = utt_value["value"]["from"]
        else:
            return True
    else:
        utt_time = utt_value["value"]
    return utt_time >= ref_time


def not_eq(utt_value: Dict[str, Any], ref_time: datetime) -> bool:
    """[summary]

    Args:
        utt_value ([type]): [description]
        ref_time (datetime): [description]

    Returns:
        bool: [description]
    """
    if isinstance(utt_value["value"], Dict):
        if "from" in utt_value["value"]:
            utt_time = utt_value["value"]["from"]
        else:
            return True
    else:
        utt_time = utt_value["value"]
    return utt_time != ref_time


def eq(utt_value: Dict[str, Any], ref_time: datetime) -> bool:
    """[summary]

    Args:
        utt_value ([type]): [description]
        ref_time (datetime): [description]

    Returns:
        bool: [description]
    """
    if isinstance(utt_value["value"], Dict):
        if "from" in utt_value["value"]:
            utt_time = utt_value["value"]["from"]
        else:
            return True
    else:
        utt_time = utt_value["value"]
    return utt_time == ref_time


def less_than_eq(utt_value: Dict[str, Any], ref_time: datetime) -> bool:
    """[summary]

    Args:
        utt_value ([type]): [description]
        ref_time (datetime): [description]

    Returns:
        bool: [description]
    """
    if isinstance(utt_value["value"], Dict):
        if "from" in utt_value["value"]:
            utt_time = utt_value["value"]["from"]
        else:
            return True
    else:
        utt_time = utt_value["value"]
    return utt_time <= ref_time


def less_than(utt_value: Dict[str, Any], ref_time: datetime) -> bool:
    """[summary]

    Args:
        utt_value ([type]): [description]
        ref_time (datetime): [description]

    Returns:
        bool: [description]
    """
    if isinstance(utt_value["value"], Dict):
        if "from" in utt_value["value"]:
            utt_time = utt_value["value"]["from"]
        else:
            return True
    else:
        utt_time = utt_value["value"]
    return utt_time < ref_time


op_set = {
    "<": less_than,
    "<=": less_than_eq,
    "==": eq,
    "!=": not_eq,
    ">=": greater_than_eq,
    ">": greater_than,
    ">today": greater_than_today,
}


def object_return(obj: Any, properties: List[str]) -> Any:
    try:
        return reduce(lambda o, k: o.get(k, {}), properties, obj)
    except KeyError:
        raise KeyError(f"Missing property in {obj}. Check the types")


def validate_type(obj: Any, obj_type: Union[type, Tuple[type]]) -> None:
    if not isinstance(obj, obj_type):
        raise TypeError(f"{obj} should be a {obj_type}")
