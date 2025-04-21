from __future__ import annotations

from domain import BaseRouterInput
from domain import RouterService
from infra.llm import LLMService
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .base import ApplicationInput
from .base import ApplicationOutput

# from domain import BaseRouterOutput
# from infra.llm import LLMBaseInput
# from infra.llm import LLMBaseOutput
# from infra.retriver import RetriverServiceV1
# from infra.solving import SolvingServiceV1

logger = get_logger(__name__)


class QuerierService(BaseService):
    settings: Settings

    @property
    def llm_service(self) -> LLMService:
        return LLMService(settings=self.settings.llm)

    @property
    def router_service(self) -> RouterService:
        return RouterService(llm_model=self.llm_service)

    # @property
    # def retrive_service(self) -> RetriverServiceV1:
    #     return RetriverServiceV1(settings=self.settings.retriveSettings)

    # @property
    # def solving_service(self) -> SolvingServiceV1:
    #     return SolvingServiceV1(settings=self.settings.solvingSettings)

    async def process(self, inputs: ApplicationInput) -> ApplicationOutput:
        router_response = await self.router_service.process(
            BaseRouterInput(query=inputs.query),
        )
        route = router_response.route.split(':')[1]
        return ApplicationOutput(
            answer=route,
            prompt_tokens=router_response.metadata,
        )
