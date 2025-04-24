from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from shared.base import BaseModel
"""
Base Service Module

This module defines abstract base classes for services in the application.
These base classes provide a consistent interface for both synchronous and
asynchronous service implementations across the codebase.
"""


class BaseService(ABC, BaseModel):
    """
    Abstract base class for synchronous services.

    This class defines the standard interface that all synchronous service
    implementations must follow, ensuring consistent behavior and structure
    across the application.

    All concrete service implementations that operate synchronously should
    inherit from this class and implement the `process` method.
    """

    @abstractmethod
    def process(self, inputs: Any) -> Any:
        """
        Process the given inputs and produce an output.

        This abstract method must be implemented by all concrete service classes
        to define their specific processing logic.

        Args:
            inputs: The input data to be processed by the service.

        Returns:
            The processed output data.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError()


class AsyncBaseService(ABC, BaseModel):
    """
    Abstract base class for asynchronous services.

    This class defines the standard interface that all asynchronous service
    implementations must follow, ensuring consistent behavior and structure
    across the application.

    All concrete service implementations that operate asynchronously should
    inherit from this class and implement the `process` method.
    """

    @abstractmethod
    async def process(self, inputs: Any) -> Any:
        """
        Process the given inputs asynchronously and produce an output.

        This abstract method must be implemented by all concrete asynchronous
        service classes to define their specific processing logic.

        Args:
            inputs: The input data to be processed by the service.

        Returns:
            The processed output data.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError()
