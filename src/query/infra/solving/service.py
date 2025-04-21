from __future__ import annotations

from shared.settings import SolvingServiceSettings

from .base import BaseSolvingInput
from .base import BaseSolvingOutput
from .base import BaseSolvingService


class SolvingServiceV1(BaseSolvingService):
    settings: SolvingServiceSettings

    def process(self, input: BaseSolvingInput) -> BaseSolvingOutput:
        return super().process(input)
