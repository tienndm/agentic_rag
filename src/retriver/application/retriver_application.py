from __future__ import annotations

from domain.processor.answer_generator import AnswerGenerator
from domain.processor.answer_generator import AnswerGeneratorInput
from domain.processor.get_fact import GetFactInput
from domain.processor.get_fact import GetFactService
from domain.processor.memory import Memory
from domain.processor.planning import PlanningInput
from domain.processor.planning import PlanningService
from domain.processor.rerank import RerankService
from domain.processor.retrive import RetriveService
from domain.processor.sub_agent import SubAgentInput
from domain.processor.sub_agent import SubAgentService
from domain.processor.web_searching import WebSearchingService
from infra.embed import EmbedService
from infra.llm import LLMService
from infra.milvus import MilvusService
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .base import ApplicationInput
from .base import ApplicationOutput

# from domain.processor.sub_agent import SubAgentInput

logger = get_logger(__name__)


class RetriveApplication(BaseService):
    settings: Settings

    @property
    def memory(self) -> Memory:
        return Memory()

    @property
    def llm_service(self) -> LLMService:
        return LLMService(settings=self.settings.llm)

    @property
    def embed_service(self) -> EmbedService:
        return EmbedService(settings=self.settings.embed)

    @property
    def rerank_service(self) -> RerankService:
        return RerankService(settings=self.settings.rerank)

    @property
    def get_fact(self) -> GetFactService:
        return GetFactService(llm_model=self.llm_service)

    @property
    def planing(self) -> PlanningService:
        return PlanningService(llm_model=self.llm_service)

    @property
    def retrive(self) -> RetriveService:
        milvus_service = MilvusService(
            settings=self.settings.milvus,
            embed_service=self.embed_service,
        )
        return RetriveService(milvus_service=milvus_service)

    @property
    def answer_generator(self) -> AnswerGenerator:
        return AnswerGenerator(llm_model=self.llm_service)

    @property
    def web_searching(self) -> WebSearchingService:
        return WebSearchingService(
            llm_model=self.llm_service,
            settings=self.settings.llm,
        )

    @property
    def sub_agent(self) -> SubAgentService:
        return SubAgentService(
            settings=self.settings,
            llm_service=self.llm_service,
            web_search_service=self.web_searching,
            retrive_service=self.retrive,
            rerank_service=self.rerank_service,
        )

    async def process(self, inputs: ApplicationInput) -> ApplicationOutput:
        self.memory.clear_memory()
        for i in range(self.settings.retrive.max_tries):
            fact_response = await self.get_fact.process(
                GetFactInput(
                    query=inputs.query,
                ),
            )
            self.memory.set_memory('fact', fact_response.fact)
            logger.info(f'Fact need to get: {fact_response.fact}')

            plan = await self.planing.process(
                PlanningInput(
                    query=inputs.query,
                    fact=fact_response.fact,
                ),
            )
            self.memory.set_memory('plan', plan)

            contexts = []
            for step_metadata in plan.plan:
                if step_metadata['agent'] == 'sub-agent':
                    step_output = await self.sub_agent.process(
                        SubAgentInput(
                            step=step_metadata['question'],
                        ),
                    )
                contexts.append(
                    {
                        'query': step_metadata['question'],
                        'content': step_output.info,
                    },
                )

            final_answer = self.answer_generator.process(
                AnswerGeneratorInput(
                    query=inputs.query,
                    context=str(contexts),
                ),
            )

            return ApplicationOutput(
                answer=final_answer.answer,
                metadata=None,
            )

        return ApplicationOutput(
            answer='',
            metadata=None,
        )
