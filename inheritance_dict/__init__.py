"""
The module defines an InheritanceDict, which is a dictionary, but for lookups where the key is a
type, it will walk over the Method Resolution Order (MRO) looking for a value.
"""

from collections.abc import Iterable

__all__ = [
    "concatMap",
    "BaseDict",
    "FallbackMixin",
    "InheritanceDict",
    "FallbackInheritanceDict",
    "TypeConvertingInheritanceDict",
    "FallbackTypeConvertingInheritanceDict",
]

MISSING = object()


def concatMap(func, items):
    """
    Yield all elements produced by applying func to each item in items.
    
    Parameters:
        func (Callable[[T], Iterable[U]]): A function that takes an item and returns an iterable of results.
        items (Iterable[T]): Iterable of input items to map over.
    
    Yields:
        U: Each element from the iterables returned by func for each item, in order.
    
    Notes:
        Equivalent to itertools.chain.from_iterable(map(func, items)). The function `func` must return an iterable for every item.
    """
    for item in items:
        yield from func(item)


class BaseDict(dict):
    """
    A dictionary that for type lookups, will walk over the Method Resolution Order (MRO) of that
    type, to find the value for the most specific superclass (including the class itself) of that
    type.
    """

    def _get_keys(self, key) -> Iterable[object]:
        """
        Return an iterable of candidate lookup keys for the given key.
        
        For the base implementation this yields only the exact key (i.e., a one-tuple containing `key`).
        Subclasses may override to expand this (for example, to yield a type's MRO or to handle tuple keys).
        """
        return (key,)

    def __getitem__(self, key):
        """
        Return the value for key, resolving through candidate keys produced by _get_keys (for example, a type's MRO).
        
        Iterates candidates yielded by self._get_keys(key) and returns the first mapped value found. If no candidate has a mapping, raises KeyError(key).
        """
        for item in self._get_keys(key):
            result = super().get(item, MISSING)
            if result is not MISSING:
                return result
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
        Return a canonical string representation of the mapping.

        The format is "<ClassName>(<dict-repr>)", where <ClassName> is the runtime class
        name (e.g., "InheritanceDict" or a subclass) and <dict-repr> is the underlying
        dictionary's repr() value.

        Returns:
            str: The formatted representation.
        """
        return f"{type(self).__name__}({super().__repr__()})"


class FallbackMixin:
    def _get_keys(self, key) -> Iterable[object]:
        """
        Return candidate lookup keys, expanding tuple keys by concatenating each element's candidates.
        
        If `key` is a tuple, this returns a flattened iterable obtained by calling `super()._get_keys`
        for each element of the tuple and yielding all results in sequence. If `key` is not a tuple,
        delegates to `super()._get_keys(key)`.
        
        Parameters:
            key: The lookup key which may be a single object or a tuple of objects.
        
        Returns:
            An iterable of candidate keys to try for lookup (may be lazy).
        """
        if isinstance(key, tuple):
            return concatMap(super()._get_keys, key)
        return super()._get_keys(key)


class InheritanceDict(BaseDict):
    def _get_keys(self, key) -> Iterable[object]:
        """
        Return candidate lookup keys for resolving `key`, including its type MRO when appropriate.
        
        If `key` is a type, yields candidates by iterating the type's method resolution order (MRO) in order and applying super()._get_keys to each class; otherwise delegates to super()._get_keys(key). The returned iterable is meant to be consumed by dictionary lookup logic that should consider a type's inheritance chain when resolving a key.
        """
        if isinstance(key, type):
            return concatMap(super()._get_keys, key.__mro__)
        return super()._get_keys(key)


class FallbackInheritanceDict(FallbackMixin, BaseDict):
    pass


class TypeConvertingInheritanceDict(InheritanceDict):
    """
    A variant of InheritanceDict that, on a missing direct lookup for non-type keys,
    retries the lookup using the key's type and resolves via that type's MRO.
    """

    def _get_keys(self, key):
        """
        Yield candidate lookup keys for a lookup, including the key's type MRO when the key is not a type.
        
        For type keys, delegates to the superclass candidate generator (usually producing that type's MRO). For non-type keys, yields candidates for the exact key first (via the superclass) and then yields candidates derived from type(key) (allowing matches defined for the value's type or its base types).
        
        Parameters:
            key: The lookup key. If not a `type`, this generator also yields candidates produced for `type(key)`.
        
        Yields:
            Candidate keys (types or other objects) in the order they should be tried for lookup.
        """
        yield from super()._get_keys(key)
        if not isinstance(key, type):
            yield from super()._get_keys(type(key))


class FallbackTypeConvertingInheritanceDict(FallbackMixin, BaseDict):
    pass
