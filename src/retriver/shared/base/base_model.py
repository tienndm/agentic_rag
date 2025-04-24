from __future__ import annotations

from pydantic import BaseModel
"""
Base Model Module

This module defines the foundation model class that all data models
in the application inherit from, providing common functionality and
configuration for data validation and serialization.
"""


class CustomBaseModel(BaseModel):
    """
    Base model class for all data models in the application.

    This class extends Pydantic's BaseModel to provide custom configuration
    and behavior specific to the application's needs. All data models
    should inherit from this class rather than directly from Pydantic's BaseModel.
    """
    class Config:
        """Configuration of the Pydantic Object"""

        # Allowing arbitrary types for class validation
        arbitrary_types_allowed = True
