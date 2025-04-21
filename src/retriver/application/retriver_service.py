from __future__ import annotations

from domain.processor.answer_generator import AnswerGenerator
from domain.processor.get_fact import GetFactInput
from domain.processor.get_fact import GetFactService
from domain.processor.memory import Memory
from domain.processor.planning import PlanningInput
from domain.processor.planning import PlanningService
from domain.processor.retrive import RetriveService
from infra.llm import LLMService
from infra.milvus import MilvusService
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .base import ApplicationInput
from .base import ApplicationOutput
# from domain.processor.retrive import RetriveInput

logger = get_logger(__name__)


class RetriveApplication(BaseService):
    settings: Settings
    memory: Memory

    @property
    def llm_service(self) -> LLMService:
        return LLMService(settings=self.settings.llm_settings)

    @property
    def milvus_service(self) -> MilvusService:
        return MilvusService(settings=self.settings.milvus_settings)

    @property
    def get_fact(self) -> GetFactService:
        return GetFactService(llm_model=self.llm_service)

    @property
    def planing(self) -> PlanningService:
        return PlanningService(llm_model=self.llm_service)

    @property
    def retrive(self) -> RetriveService:
        return RetriveService(settings=self.settings.milvus_settings)

    @property
    def answer_generator(self) -> AnswerGenerator:
        return AnswerGenerator(llm_model=self.llm_service)

    def process(self, inputs: ApplicationInput) -> ApplicationOutput:
        self.memory.clear_memory()
        for i in range(self.settings.retrive_settings.max_tries):
            fact = self.get_fact.process(
                GetFactInput(
                    query=inputs.query,
                ),
            )
            self.memory.set_memory('fact', fact)

            plan = self.planing.process(
                PlanningInput(
                    query=inputs.query,
                    fact=fact,
                ),
            )
            self.memory.set_memory('plan', plan)

            # TODO parse plan
            # context = self.retrive.process(
            #     RetriveInput(
            #         query=list(plan),
            #     ),
            # )

            # TODO rerank + source_selector

            # TODO final_answer

            # TODO validation_answer

        return ApplicationOutput(
            answer='',
            metadata=None,
        )
