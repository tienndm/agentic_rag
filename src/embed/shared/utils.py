from __future__ import annotations

from functools import lru_cache

from .settings import Settings


@lru_cache
def get_settings():
    """Get application settings with caching.

    This function returns the application settings singleton instance.
    It uses lru_cache decorator to cache the result, ensuring that
    settings are only loaded once during the application lifetime.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
