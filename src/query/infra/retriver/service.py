from __future__ import annotations

from shared.settings import RetriveServiceSettings

from .base import BaseRetriveInput
from .base import BaseRetriveOutput
from .base import BaseRetriveService


class RetriverServiceV1(BaseRetriveService):
    settings: RetriveServiceSettings

    def process(self, input: BaseRetriveInput) -> BaseRetriveOutput:
        return super().process(input)
