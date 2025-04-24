from __future__ import annotations

"""
Memory Module

This module provides functionality for maintaining transient state during
the processing of queries, allowing different components to share information.
"""


class Memory:
    """
    Singleton class for storing and retrieving transient data during processing.

    This class implements a simple in-memory key-value store that allows different
    components of the system to share information during the processing of a query.
    It maintains state for facts extracted from queries, execution plans,
    generated code, and execution results.

    The memory is designed to be cleared between processing different queries to
    prevent information leakage between unrelated operations.
    """

    memory = {
        'fact': None,
        'plan': None,
        'code': None,
        'execution_result': None,
    }

    @classmethod
    def set_memory(cls, key, value):
        """
        Store a value in memory under the specified key.

        Args:
            key: The key under which to store the value.
            value: The value to store in memory.
        """
        cls.memory[key] = value

    @classmethod
    def get_memory(cls, key):
        """
        Retrieve a value from memory by its key.

        Args:
            key: The key of the value to retrieve.

        Returns:
            The value stored under the specified key, or None if the key doesn't exist.
        """
        return cls.memory.get(key)

    @classmethod
    def clear_memory(cls):
        """
        Reset the memory to its initial state.

        This method clears all stored values, resetting them to None. It should be
        called between processing different queries to prevent information leakage.
        """
        cls.memory = {
            'fact': None,
            'plan': None,
            'code': None,
            'execution_result': None,
        }
