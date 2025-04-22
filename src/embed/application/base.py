from __future__ import annotations

from shared.base import BaseModel


class ApplicationInput(BaseModel):
    """Base input model for application layer.

    This model defines the standard input structure expected by application services.

    Attributes:
        query (list[str]): List of text strings to be processed by the application
    """

    query: list[str]


class ApplicationOutput(BaseModel):
    """Base output model for application layer.

    This model defines the standard output structure returned by application services.
    The structure follows a format similar to common embedding API responses.

    Attributes:
        data (list[dict]): List of processed data items (e.g., embedding vectors)
        model (str, optional): Name of the model used for processing. Defaults to None.
        object (str): Type of the returned object. Defaults to 'list'.
        usage (dict, optional): Usage statistics for the request. Defaults to None.
    """

    data: list[dict]
    model: str | None = None
    object: str = 'list'
    usage: dict | None = None
