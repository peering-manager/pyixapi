class Hashabledict(dict):
    def __hash__(self):
        return hash(frozenset(self))


def cat(*args, separator="/", trailing=""):
    """
    Concatenate strings given a separator. All items will be parsed as string.

    If the separator is found at the beginning or the end of a string to concatenate,
    it'll be removed to avoid double separators in the final result.

    If an item cannot be parsed as a string, an AttributeError will be raised.

    >>> concatenate("a", "b", "c")
    'a/b/c/'
    >>> concatenate("a", "b", "/c/", separator="")
    'a/b/c'
    >>> concatenate("a", "/b/", 1)
    'a/b/1/'
    >>> concatenate("a", "b", "c", separator="_", trailing="_")
    'a_b_c_'
    """
    s = separator.join([str(i).lstrip(separator).rstrip(separator) for i in args])
    if trailing:
        s += trailing
    return s
