from typing import Any


class Hashabledict(dict):  # type: ignore[type-arg]
    def __hash__(self) -> int:
        return hash(frozenset(self))


def cat(*args: Any, separator: str = "/", trailing: str = "") -> str:
    """
    Concatenate strings given a separator. All items will be parsed as string.

    If the separator is found at the beginning or the end of a string to concatenate,
    it'll be removed to avoid double separators in the final result.

    If an item cannot be parsed as a string, an AttributeError will be raised.

    >>> cat("a", "/b/", "c/")
    'a/b/c'
    >>> cat("a", 1, "b")
    'a/1/b'
    >>> cat("a", "b", "c", separator="_")
    'a_b_c'
    >>> cat("a", "b", "c", trailing="/")
    'a/b/c/'
    """
    s = separator.join([str(i).strip(separator) for i in args if str(i)])
    if trailing:
        s += trailing
    return s
