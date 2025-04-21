from __future__ import annotations

from .router.service import BaseRouterInput
from .router.service import BaseRouterOutput
from .router.service import RouterServiceV1 as RouterService

__all__ = [
    'RouterService',
    'BaseRouterInput',
    'BaseRouterOutput',
]
