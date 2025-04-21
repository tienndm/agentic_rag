from __future__ import annotations
SYSTEM_PROMPT = """
<role>You are an AI assistant providing factual information based on user queries.</role>

<goal>
Extract accurate and relevant facts from user queries to support subsequent planning and execution.
Focus on identifying key information that will be useful for solving the user's problem.
</goal>
"""

USER_PROMPT = """
<instruction>
Extract the key factual information from this query: {query}

Provide a concise summary of the essential facts that would be necessary to answer this query.
Focus only on extractual information, relevant concepts, and potential approaches.
</instruction>
"""
