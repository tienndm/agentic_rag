from __future__ import annotations

from domain.processor.rerank import RerankInput
from domain.processor.rerank import RerankService
from domain.processor.web_searching import WebSearchingInput
from domain.processor.web_searching import WebSearchingService
from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMService
from infra.llm import MessageRole
from infra.milvus_clone import MilvusService
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger
from shared.settings import Settings

from .prompt.decide_tool import DECIDE_TOOL_SYSTEM_PROMPT
from .prompt.decide_tool import DECIDE_TOOL_USER_PROMPT

logger = get_logger(__name__)


class SubAgentInput(BaseModel):
    step: str


class SubAgentOutput(BaseModel):
    info: str
    metadata: dict[str, str] | None = None


class SubAgentService(BaseService):
    settings: Settings
    llm_service: LLMService
    milvus_service: MilvusService
    web_search_service: WebSearchingService
    rerank_service: RerankService

    async def decide_tool(self, step: str) -> str:
        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM, content=DECIDE_TOOL_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=DECIDE_TOOL_USER_PROMPT.format(query=step),
            ),
        ]

        response = await self.llm_service.process(
            LLMBaseInput(
                messages=messages,
            ),
        )
        tool = response.response.strip().lower()
        logger.info(f'Decided to use tool: {tool} for step: {step}')
        return tool

    async def process(self, inputs: SubAgentInput) -> SubAgentOutput:
        try:
            tool = await self.decide_tool(inputs.step)
        except Exception as e:
            logger.exception(
                f'Error while deciding tool: {e}',
                extra={
                    'inputs': inputs,
                },
            )
            raise e

        contexts = []
        if tool == 'web_search':
            web_search_output = await self.web_search_service.process(
                WebSearchingInput(
                    query=inputs.step,
                    fetch_content=True,
                ),
            )
            for source in web_search_output.sources:
                contexts.append(
                    {
                        'title': source.get('title', ''),
                        'url': source.get('url', ''),
                        'content': source.get('content', ''),
                        'source_type': 'web_search',
                    },
                )
            if web_search_output.answer:
                return SubAgentOutput(
                    info=web_search_output.answer,
                    metadata={
                        'source': 'web_search',
                        'sources_count': str(len(web_search_output.sources)),
                    },
                )

        elif tool == 'vector_db':
            # vector_db_output = self.milvus_service.process(
            # )
            raise NotImplementedError()
        else:
            logger.exception(
                f'Error while decided tool: {tool}',
                extra={
                    'inputs': inputs,
                },
            )
            raise ValueError(f'Unsupported tool: {tool}')

        if not contexts:
            logger.warning(f'No contexts found for step: {inputs.step}')
            return SubAgentOutput(
                info=f'No information found for: {inputs.step}',
                metadata={'source': 'none', 'error': 'no_contexts'},
            )

        try:
            rerank_input = RerankInput(
                query=inputs.step,
                contexts=contexts,
                top_k=self.settings.retrive.top_k or 3,
            )

            rerank_output = await self.rerank_service.process(rerank_input)
            ranked_contexts = rerank_output.ranked_contexts
        except Exception as e:
            logger.exception(
                f'Error during reranking: {e}',
                extra={
                    'inputs': inputs,
                    'contexts_count': len(contexts),
                },
            )
            ranked_contexts = contexts[: min(len(contexts), 3)]

        try:
            consolidated_info = self._create_consolidated_info(
                inputs.step, ranked_contexts,
            )
            return SubAgentOutput(
                info=consolidated_info,
                metadata={
                    'source': tool,
                    'contexts_count': str(len(contexts)),
                    'ranked_contexts_count': str(len(ranked_contexts)),
                },
            )
        except Exception as e:
            logger.exception(
                f'Error creating consolidated info: {e}',
                extra={
                    'inputs': inputs,
                },
            )

            consolidated_text = '\n\n'.join(
                [
                    f"Source: {ctx.get('title', 'Unknown')} ({ctx.get('url', 'No URL')})\n{ctx.get('content', 'No content')[:500]}..."
                    for ctx in ranked_contexts[:3]
                ],
            )

            return SubAgentOutput(
                info=consolidated_text,
                metadata={
                    'source': tool,
                    'error': 'consolidation_failed',
                    'contexts_count': str(len(contexts)),
                },
            )

    async def _create_consolidated_info(self, query: str, contexts: list[dict]) -> str:
        """Create a consolidated answer from the ranked contexts."""
        if not contexts:
            return f'No information found for: {query}'

        context_texts = []
        for i, ctx in enumerate(contexts[:5]):
            content = ctx.get('content', '').strip()
            if content:
                source = f"{ctx.get('title', 'Unknown')} ({ctx.get('url', 'No URL')})"
                context_texts.append(
                    f'[Source {i+1}]: {source}\n{content[:1000]}...',
                )

        context_str = '\n\n'.join(context_texts)

        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM,
                content="""You are an expert researcher who synthesizes information from multiple sources into clear,
                concise summaries. Create a comprehensive answer based on the provided sources, being faithful to the
                information in the sources. Cite source numbers [Source X] where appropriate. If the sources contradict
                each other, acknowledge this and explain the different perspectives.""",
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=f"""Query: {query}

Please synthesize the following sources to answer the query:

{context_str}

Provide a comprehensive answer based solely on the information in these sources.""",
            ),
        ]

        try:
            response = await self.llm_service.process(LLMBaseInput(messages=messages))
            return response.response
        except Exception as e:
            logger.exception(f'Error generating consolidated answer: {e}')
            return (
                f'Error synthesizing information from {len(contexts)} sources: {str(e)}'
            )
