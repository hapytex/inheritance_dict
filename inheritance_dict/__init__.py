"""
The module defines an InheritanceDict, which is a dictionary, but for lookups where the key is a
type, it will walk over the Method Resolution Order (MRO) looking for a value.
"""


class InheritanceDict(dict):
    """
    A dictionary that for type lookups, will walk over the Method Resolution Order (MRO) of that
    type, to find the value for the most specific superclass (including the class itself) of that
    type.
    """

    def __getitem__(self, key):
        """
        Return the value associated with a key, resolving class inheritance for type keys.

        If `key` is a class (a `type`), this looks up values for each class in the key's
        method resolution order (MRO) and returns the first found mapping value.
        If `key` is not a class, it is used directly as the lookup key.

        Parameters:
            key: The lookup key. If a `type`, the MRO (key.__mro__) is searched in order;
            otherwise `key` itself is used.

        Returns:
            The mapped value for the first matching key.

        Raises:
            KeyError: If no matching key is found.
        """
        if isinstance(key, type):
            items = key.__mro__
        else:
            items = (key,)
        for item in items:
            try:
                return super().__getitem__(item)
            except KeyError:
                pass
        raise KeyError(key)

    def get(self, key, default=None):
        """
        Return the value mapped to `key` or `default` if no mapping exists.

        If `key` is a type, the lookup walks the type's MRO (including the type itself) and returns
        the first matching value; for non-type keys a direct lookup is attempted. If no candidate
        is found, `default` is returned.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        """
        Return the value for `key` if present; otherwise insert `default` for `key` and return it.

        This method uses the same lookup semantics as __getitem__: if `key` is a type, the mapping
        is searched along the key's MRO and the first matching value is returned. If no mapping is
        found, `default` is stored under the exact `key` provided (no MRO walking when writing)
        and `default` is returned.

        Parameters:
            key: The lookup key (may be a type; type keys are resolved via MRO on read).
            default: Value to insert and return if no existing mapping is found.

        Returns:
            The existing mapped value (found via lookup) or `default` after insertion.
        """
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def __repr__(self):
        """
        Return the canonical string representation of the InheritanceDict.

        Returns:
            str: A representation in the form "InheritanceDict(<dict-repr>)", where <dict-repr> is
                 the underlying dict's repr.
        """
        return f"{type(self).__name__}({super().__repr__()})"


class TypeConvertingInheritanceDict(InheritanceDict):
    """
    @coderabbitai generate docstrings
    """
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            if not isinstance(key, type):
                key = type(key)
                return super().__getitem__(key)
            raise
