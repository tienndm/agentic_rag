from __future__ import annotations

from shared.base import BaseModel
"""
Application Base Module

This module defines the base input and output models used by the application.
These models represent the standard interface for information flowing into
and out of the retrieval system.
"""


class ApplicationInput(BaseModel):
    """
    Base input model for the application.

    This model represents the standard input interface for the retrieval system,
    containing the user's query that needs to be processed.

    Attributes:
        query (str): The user's query to be processed by the application.
    """

    query: str


class ApplicationOutput(BaseModel):
    """
    Base output model for the application.

    This model represents the standard output interface for the retrieval system,
    containing the generated answer and optional metadata.

    Attributes:
        answer (str): The generated answer to the user's query.
        metadata (dict[str, str] | None): Optional metadata about the answer generation process.
    """

    answer: str
    metadata: dict[str, str] | None = None
