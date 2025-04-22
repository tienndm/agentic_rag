from __future__ import annotations

import threading


class SingletonMeta(type):
    """Thread-safe metaclass for implementing the Singleton pattern.

    This metaclass ensures that only one instance of a class is created,
    regardless of how many times the class is instantiated. It uses
    a thread lock to ensure thread safety during instance creation.

    Attributes:
        _instances (dict): Dictionary storing singleton instances
        _lock (threading.Lock): Thread lock for synchronization
    """

    _instances: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """Override the call method to implement singleton behavior.

        When a class using this metaclass is instantiated, this method
        checks if an instance already exists. If not, it creates one.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            object: The singleton instance of the class
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

    def clear(cls):
        """Remove the singleton instance from the instances dictionary.

        This method is useful for testing or when the instance needs
        to be recreated with different parameters.
        """
        with cls._lock:
            _ = cls._instances.pop(cls, None)
