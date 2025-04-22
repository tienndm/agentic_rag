from __future__ import annotations

from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    """Base model class extending Pydantic's BaseModel with custom configurations.

    This class provides a foundation for all data models in the application,
    with custom configurations to improve flexibility and functionality.

    It's used as the base class for all data models across the application
    to ensure consistent behavior and validation.
    """

    class Config:
        """Configuration of the Pydantic Object"""

        # Allowing arbitrary types for class validation
        arbitrary_types_allowed = True
