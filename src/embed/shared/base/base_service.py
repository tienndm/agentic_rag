from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from shared.base import BaseModel


class BaseService(ABC, BaseModel):
    """Abstract base class for synchronous service implementations.

    This class defines the contract that all synchronous services must implement.
    It inherits from both ABC (abstract base class) and BaseModel to provide
    both service interface definition and data validation capabilities.
    """

    @abstractmethod
    def process(self, inputs: Any) -> Any:
        """Process the input data and return the result.

        Args:
            inputs (Any): The input data to process

        Returns:
            Any: The processed result

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError()


class AsyncBaseService(ABC, BaseModel):
    """Abstract base class for asynchronous service implementations.

    This class defines the contract that all asynchronous services must implement.
    It inherits from both ABC (abstract base class) and BaseModel to provide
    both service interface definition and data validation capabilities.
    """

    @abstractmethod
    async def process(self, inputs: Any) -> Any:
        """Process the input data asynchronously and return the result.

        Args:
            inputs (Any): The input data to process

        Returns:
            Any: The processed result

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError()
