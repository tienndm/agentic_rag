from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings
from infra.llm import LLMService
from domain.answer_generator.service import AnswerGenerator
from domain.get_fact.service import GetFactService
from domain.planning.service import PlanningService

logger = get_logger(__name__)


class QuerierService(BaseService):
    settings: Settings

    @property
    def llm_service(self) -> LLMService:
        return LLMService(settings=self.settings.llmSettings)

    @property
    def answer_generator(self) -> AnswerGenerator:
        return AnswerGenerator(
            settings=self.settings.llmSettings, llm_service=self.llm_service
        )

    @property
    def get_fact(self) -> GetFactService:
        return GetFactService(
            settings=self.settings.llmSettings, llm_service=self.llm_service
        )

    @property
    def planning_service(self) -> PlanningService:
        return PlanningService(
            settings=self.settings.llmSettings, llm_service=self.llm_service
        )