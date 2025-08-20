class InheritanceDict(dict):
    def __getitem__(self, key):
        """
        Return the mapping value for key, resolving class inheritance when key is a type.
        
        If key is a class (type), this searches the class's method resolution order (key.__mro__) and returns the first mapped value found for any class in that order. If key is not a class, it is used directly for a normal lookup.
        
        Parameters:
            key: Lookup key. When a type is provided, its MRO is searched in order.
        
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
        try:
            return self[key]
        except KeyError:
            return default
