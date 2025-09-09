"""
The module defines an InheritanceDict, which is a dictionary, but for lookups where the key is a
type, it will walk over the Method Resolution Order (MRO) looking for a value.
"""

from collections.abc import Iterable

__all__ = [
    "concat_map",
    "BaseDict",
    "FallbackMixin",
    "InheritanceDict",
    "FallbackInheritanceDict",
    "TypeConvertingInheritanceDict",
    "FallbackTypeConvertingInheritanceDict",
]
MISSING = object()


def concat_map(func, items):
    """
    Yield items from the iterables produced by applying func to each element of items.

    func should be a callable that accepts a single item and returns an iterable; concat_map
    lazily iterates over items, calls func(item) for each, and yields each element from the
    resulting iterable in order.
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
        Return an iterable of candidate lookup keys for dictionary lookup.

        This default implementation yields only the original `key`. Subclasses (e.g., those that
        perform Method Resolution Order or tuple-based fallback lookups) should override this to
        produce additional candidate keys to try in order.

        Returns:
            Iterable[object]: An iterable yielding candidate keys; by default a single-item tuple
                              containing `key`.
        """
        return (key,)

    def _set_key(self, key) -> object:
        """@coderabbitai: generate docstrings"""
        return key

    def __getitem__(self, key):
        """
        Return the value mapped to `key` by trying candidate lookup keys produced by `_get_keys`.

        This performs lookups in the order produced by `self._get_keys(key)` and returns the first
        mapped value found. If no candidate is present in the mapping a `KeyError` is raised.
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
            self[self._set_key(key)] = default
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


class FallbackMixin:  # pylint: disable=too-few-public-methods
    """@coderabbitai: generate docstrings"""

    def _get_keys(self, key) -> Iterable[object]:
        """
        Return an iterable of candidate lookup keys, expanding tuple keys by concatenating
        the candidate sequences for each element.

        If `key` is a tuple, yields all items produced by applying the superclass's
        `_get_keys` to each element of the tuple (flattened in element order). If `key`
        is not a tuple, delegates to the superclass's `_get_keys`.

        Parameters:
            key: The lookup key or a tuple of lookup keys.

        Returns:
            An iterable of candidate keys to try for dictionary lookup.
        """
        if isinstance(key, tuple):
            return concat_map(super()._get_keys, key)
        return super()._get_keys(key)

    def _set_key(self, key) -> object:
        """@coderabbitai: generate docstrings"""
        if isinstance(key, tuple) and key:
            return key[0]
        return super()._set_key(key)


class InheritanceDict(BaseDict):
    """@coderabbitai: generate docstrings"""

    def _get_keys(self, key) -> Iterable[object]:
        """
        Yield lookup candidate keys.

        If `key` is a type, yields the classes in its method-resolution order (key.__mro__) in
        order; otherwise yields the key itself. Used to produce the sequence of keys to try for
        dictionary lookups that support type-based inheritance resolution.
        """
        if isinstance(key, type):
            return concat_map(super()._get_keys, key.__mro__)
        return super()._get_keys(key)


class FallbackInheritanceDict(FallbackMixin, BaseDict):
    """@coderabbitai: generate docstrings"""


class TypeConvertingInheritanceDict(InheritanceDict):
    """
    A variant of InheritanceDict that, on a missing direct lookup for non-type keys,
    retries the lookup using the key's type and resolves via that type's MRO.
    """

    def _get_keys(self, key):
        """
        Yield candidate lookup keys for a lookup key.

        Always yields the candidates produced by super()._get_keys(key). If key is not a type,
        also yields the candidates produced by super()._get_keys(type(key)) so lookups will
        fall back to the key's type (and its MRO) after the original candidates.

        Parameters:
            key: The lookup key. Non-type keys cause an additional sequence of candidate keys
                 derived from type(key).

        Yields:
            Candidate keys (types or other lookup keys) in the order they should be tried.
        """
        yield from super()._get_keys(key)
        if not isinstance(key, type):
            yield from super()._get_keys(type(key))


class FallbackTypeConvertingInheritanceDict(FallbackMixin, BaseDict):
    """@coderabbitai: generate docstrings"""
