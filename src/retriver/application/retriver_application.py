from __future__ import annotations

from domain.processor.answer_generator import AnswerGenerator
from domain.processor.answer_generator import AnswerGeneratorInput
from domain.processor.chunking import ChunkingService
from domain.processor.get_fact import GetFactInput
from domain.processor.get_fact import GetFactService
from domain.processor.memory import Memory
from domain.processor.planning import PlanningInput
from domain.processor.planning import PlanningService
from domain.processor.rerank import RerankService
from domain.processor.retrive import RetriveService
from domain.processor.sub_agent import SubAgentInput
from domain.processor.sub_agent import SubAgentService
from domain.processor.web_searching import WebSearchService
from infra.embed import EmbedService
from infra.llm import LLMService
from infra.milvus import MilvusService
from shared.base import AsyncBaseService
from shared.logging import get_logger
from shared.settings import Settings

from .base import ApplicationInput
from .base import ApplicationOutput

logger = get_logger(__name__)


class RetriveApplication(AsyncBaseService):
    """
    Main application orchestrating the retrieval-augmented generation process.

    This application coordinates various services and processors to:
    1. Extract factual information from user queries
    2. Generate execution plans for information retrieval
    3. Execute retrieval steps using appropriate sub-agents
    4. Generate final comprehensive answers based on retrieved context

    The application follows a clear workflow that integrates the LLM capabilities
    with vector search and web search to provide accurate information.
    """

    settings: Settings
    _retrive_service: RetriveService = None

    @property
    def memory(self) -> Memory:
        """Returns the Memory singleton instance for storing transient data during processing."""
        return Memory()

    @property
    def llm_service(self) -> LLMService:
        """Returns a configured LLM service instance for text generation tasks."""
        return LLMService(settings=self.settings.llm)

    @property
    def embed_service(self) -> EmbedService:
        """Returns a configured embedding service for text vectorization."""
        return EmbedService(settings=self.settings.embed)

    @property
    def rerank_service(self) -> RerankService:
        """Get or create the RerankService singleton instance."""
        return RerankService(settings=self.settings.rerank)

    @property
    def get_fact(self) -> GetFactService:
        """Returns a service for extracting key facts from user queries."""
        return GetFactService(llm_model=self.llm_service)

    @property
    def planing(self) -> PlanningService:
        """Returns a service for generating retrieval execution plans."""
        return PlanningService(llm_model=self.llm_service)

    async def get_retrive_service(self) -> RetriveService:
        """
        Lazily initializes and returns the retrieval service.

        The service is initialized only once and reused for subsequent calls.

        Returns:
            RetriveService: A configured retrieval service connected to the vector database
        """
        if self._retrive_service is None:
            milvus_service = MilvusService(
                settings=self.settings.milvus,
                embed_service=self.embed_service,
            )
            self._retrive_service = RetriveService(milvus_service=milvus_service)
        return self._retrive_service

    @property
    def answer_generator(self) -> AnswerGenerator:
        """Returns a service for generating final answers from retrieved contexts."""
        return AnswerGenerator(llm_model=self.llm_service)

    @property
    def web_searching(self) -> WebSearchService:
        """Returns a service for performing web searches and processing results."""
        return WebSearchService(
            settings=self.settings.web_search,
            llm_service=self.llm_service,
            chunking_service=self.chunking_service,
        )

    @property
    def chunking_service(self) -> ChunkingService:
        """Returns a service for text chunking operations based on semantic similarity."""
        return ChunkingService(
            settings=self.settings.chunking,
            embed_service=self.embed_service,
        )

    async def get_sub_agent(self) -> SubAgentService:
        """
        Creates and returns a configured SubAgentService.

        The sub-agent integrates multiple retrieval strategies and can dynamically
        choose between them based on the query.

        Returns:
            SubAgentService: A configured sub-agent service
        """
        retrive_service = await self.get_retrive_service()
        return SubAgentService(
            settings=self.settings,
            llm_service=self.llm_service,
            web_search_service=self.web_searching,
            retrive_service=retrive_service,
            rerank_service=self.rerank_service,
        )

    async def process(self, inputs: ApplicationInput) -> ApplicationOutput:
        """
        Process a user query through the retrieval-augmented generation pipeline.

        This method implements the core workflow:
        1. Extract facts from the query
        2. Generate an execution plan
        3. Execute plan steps with appropriate sub-agents
        4. Consolidate retrieved information
        5. Generate a comprehensive answer

        Args:
            inputs: The application input containing the user query

        Returns:
            ApplicationOutput: The final answer generated from retrieved context
        """
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
                    sub_agent = await self.get_sub_agent()
                    step_output = await sub_agent.process(
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

            final_answer = await self.answer_generator.process(
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
