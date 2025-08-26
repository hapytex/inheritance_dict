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
        Return the canonical string representation of this mapping.
        
        The result is a string of the form "<ClassName>(<dict-repr>)", where <ClassName>
        is the runtime class name (e.g., "InheritanceDict" or a subclass name) and
        <dict-repr> is the underlying dict's repr.
        
        Returns:
            str: The canonical representation.
        """
        return f"{type(self).__name__}({super().__repr__()})"


class TypeConvertingInheritanceDict(InheritanceDict):
    def __getitem__(self, key):
        """
        Return the value for `key`, falling back to `type(key)` for non-type keys on a miss.
        
        Performs the normal InheritanceDict lookup (which for type keys walks the type's MRO). If that lookup raises KeyError and the original `key` is not a type, this method will retry the lookup using `type(key)` and return the result if found.
        
        Parameters:
            key: A mapping key or an object whose type may be used for lookup.
        
        Returns:
            The mapped value for `key`, or for `type(key)` when the initial lookup fails for non-type keys.
        
        Raises:
            KeyError: If no mapping exists for `key`, and (for non-type keys) no mapping exists for `type(key)`.
        """
        try:
            return super().__getitem__(key)
        except KeyError:
            if not isinstance(key, type):
                key = type(key)
                return super().__getitem__(key)
            raise
