from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from infra.llm import CompletionMessage
from infra.llm import LLMBaseInput
from infra.llm import LLMService
from infra.llm import MessageRole
from shared.base import BaseModel
from shared.base import BaseService
from shared.logging import get_logger

logger = get_logger(__name__)

MERGE_CONTEXT_SYSTEM_PROMPT = """
<role>Bạn là một chuyên gia tổng hợp và quản lý thông tin.</role>

<goal>
Hợp nhất và tóm tắt thông tin từ nhiều nguồn thành một tài liệu mạch lạc và đầy đủ.
</goal>

<constraints>
- Loại bỏ thông tin trùng lặp
- Kết hợp thông tin liên quan với nhau
- Sắp xếp thông tin theo trình tự logic
- Giữ lại tất cả thông tin giá trị, không bỏ sót chi tiết quan trọng
- Duy trì tính chính xác của thông tin gốc
</constraints>

<instructions>
Dựa vào câu truy vấn và thông tin đã thu thập, hãy tổng hợp thành một văn bản mạch lạc, đầy đủ.
Thông tin mới chỉ nên được sử dụng để bổ sung vào thông tin hiện có, không thay thế hoàn toàn.
Đảm bảo tính nhất quán và loại bỏ mọi mâu thuẫn giữa các nguồn thông tin.
</instructions>
"""

MERGE_CONTEXT_USER_PROMPT = """
<query>
{query}
</query>

<existing_information>
{existing_info}
</existing_information>

<new_information>
{new_info}
</new_information>

Hãy tổng hợp tất cả thông tin trên thành một văn bản hoàn chỉnh, đầy đủ và mạch lạc.
"""


class MemoryManagerInput(BaseModel):
    """
    Input model for the MemoryManager service.

    Attributes:
        query_id: Unique identifier for the query/conversation
        action: The action to perform (merge, get, update, clear)
        query: Original query text (for merging)
        context: New context to merge (for merging)
        step: Step identifier (for caching)
        missing_aspects: List of missing information aspects (for updating)
    """

    query_id: str
    action: str  # merge, get, update, clear, cache, get_cache
    query: str = ''
    context: str = ''
    step: str = ''
    missing_aspects: List[str] = []


class MemoryManagerOutput(BaseModel):
    """
    Output model for the MemoryManager service.

    Attributes:
        result: The result of the memory operation
        metadata: Additional metadata about the operation
    """

    result: str | Dict[str, Any] | None = None
    metadata: Dict[str, Any] = {}


class InformationMemory(BaseModel):
    """
    Model for storing and tracking information retrieved during processing.

    Attributes:
        complete_info: The consolidated information gathered so far
        missing_aspects: Specific aspects of information still missing
        original_query: The original query that initiated the search
    """

    complete_info: str = ''
    missing_aspects: List[str] = []
    original_query: str = ''
    cached_contexts: Dict[str, Any] = {}


class MemoryManager(BaseService):
    """
    Service for managing memory of retrieved information across queries.

    Handles storing, retrieving, and merging contexts from different searches.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_service: Optional[LLMService] = None
    memories: Dict[str, InformationMemory] = {}

    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm_service = llm_service
        self.memories = {}

    async def process(self, inputs: MemoryManagerInput) -> MemoryManagerOutput:
        """
        Process a memory operation based on the specified action.

        Args:
            inputs: The MemoryManagerInput containing the action and parameters

        Returns:
            MemoryManagerOutput: The result of the memory operation
        """
        try:
            if inputs.action == 'merge':
                result = await self.merge_contexts(
                    query_id=inputs.query_id,
                    query=inputs.query,
                    new_context=inputs.context,
                )
                return MemoryManagerOutput(
                    result=result,
                    metadata={
                        'prompt_tokens': self.prompt_tokens,
                        'completion_tokens': self.completion_tokens,
                        'total_tokens': self.total_tokens,
                    },
                )

            elif inputs.action == 'get':
                memory = self.get_memory(inputs.query_id)
                return MemoryManagerOutput(
                    result=memory.complete_info,
                    metadata={
                        'missing_aspects': memory.missing_aspects,
                        'original_query': memory.original_query,
                    },
                )

            elif inputs.action == 'update':
                self.update_missing_aspects(inputs.query_id, inputs.missing_aspects)
                return MemoryManagerOutput(result='Missing aspects updated')

            elif inputs.action == 'clear':
                self.clear_memory(inputs.query_id)
                return MemoryManagerOutput(result='Memory cleared')

            elif inputs.action == 'cache':
                if not isinstance(inputs.context, dict) and inputs.context:
                    context_dict = {'content': inputs.context}
                else:
                    context_dict = inputs.context

                self.cache_context(inputs.query_id, inputs.step, context_dict)
                return MemoryManagerOutput(result='Context cached')

            elif inputs.action == 'get_cache':
                result = self.get_cached_context(inputs.query_id, inputs.step)
                return MemoryManagerOutput(result=result)

            else:
                return MemoryManagerOutput(
                    result=None, metadata={'error': 'Invalid action'},
                )

        except Exception as e:
            logger.exception(f'Error in memory manager: {e}')
            return MemoryManagerOutput(result=None, metadata={'error': str(e)})

    def get_memory(self, query_id: str) -> InformationMemory:
        """
        Get the memory for a specific query ID, creating it if it doesn't exist.

        Args:
            query_id: Unique identifier for the query/conversation

        Returns:
            InformationMemory: The memory object for the specified query
        """
        if query_id not in self.memories:
            self.memories[query_id] = InformationMemory()

        return self.memories[query_id]

    def clear_memory(self, query_id: str) -> None:
        """
        Clear the memory for a specific query ID.

        Args:
            query_id: Unique identifier for the query/conversation
        """
        if query_id in self.memories:
            del self.memories[query_id]

    async def merge_contexts(self, query_id: str, query: str, new_context: str) -> str:
        """
        Merge new context with existing information in memory.

        Args:
            query_id: Unique identifier for the query/conversation
            query: The original query text
            new_context: New information to be merged

        Returns:
            str: The merged context
        """
        memory = self.get_memory(query_id)

        # If we don't have any existing information, just use the new context
        if not memory.complete_info:
            memory.complete_info = new_context
            memory.original_query = query
            return new_context

        # If we have existing info, merge it with new context
        messages = [
            CompletionMessage(
                role=MessageRole.SYSTEM,
                content=MERGE_CONTEXT_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=MessageRole.USER,
                content=MERGE_CONTEXT_USER_PROMPT.format(
                    query=query,
                    existing_info=memory.complete_info,
                    new_info=new_context,
                ),
            ),
        ]

        response = await self.llm_service.process(
            LLMBaseInput(messages=messages),
        )

        merged_context = response.response.strip()

        self.prompt_tokens += int(response.metadata['prompt_tokens'])
        self.completion_tokens += int(response.metadata['completion_tokens'])
        self.total_tokens += int(response.metadata['total_tokens'])

        # Update memory with merged context
        memory.complete_info = merged_context

        return merged_context

    def update_missing_aspects(self, query_id: str, missing_aspects: List[str]) -> None:
        """
        Update the list of missing aspects for a given memory.

        Args:
            query_id: Unique identifier for the query/conversation
            missing_aspects: List of specific information aspects still missing
        """
        memory = self.get_memory(query_id)
        memory.missing_aspects = missing_aspects

    def cache_context(self, query_id: str, step: str, context: Dict[str, Any]) -> None:
        """
        Cache retrieved context for a specific step.

        Args:
            query_id: Unique identifier for the query/conversation
            step: The specific query step
            context: The retrieved context information
        """
        memory = self.get_memory(query_id)
        memory.cached_contexts[step] = context

    def get_cached_context(self, query_id: str, step: str) -> Optional[Dict[str, Any]]:
        """
        Get previously cached context for a specific step.

        Args:
            query_id: Unique identifier for the query/conversation
            step: The specific query step

        Returns:
            Optional[Dict[str, Any]]: The cached context if available, None otherwise
        """
        memory = self.get_memory(query_id)
        return memory.cached_contexts.get(step)
