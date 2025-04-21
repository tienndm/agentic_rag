from __future__ import annotations
SYSTEM_PROMPT = """
<role>You are an expert Python programmer and problem-solving assistant.</role>

<goal>
Create a detailed plan that will solve the user's query based on provided facts. Your plan will be converted into executable Python code.
</goal>

<guidelines>
- Focus on generating a clear, step-by-step plan that can be easily translated into Python code
- Be specific about libraries and techniques to use
- Consider error handling and edge cases
- Use standard Python libraries when possible
</guidelines>
"""

USER_PROMPT = """
<instruction>
Based on this query: {query}

And these facts: {fact}

Create a detailed plan for solving this problem with Python code. Break down the solution into clear logical steps. Include:
1. What libraries to import
2. What data structures to use
3. How to implement each step of the solution
4. How to handle potential errors or edge cases
5. How to present the final result

Be specific and thorough so your plan can be directly translated into executable Python code.
</instruction>
"""

RETRY_PROMPT = """
<instruction>
Based on this query: {query}

And these facts: {fact}

My previous plan was:
{previous_plan}

However, this plan wasn't optimal. Please provide an improved plan, focusing on:
1. Any logical improvements that could be made
2. Better algorithm or approach choices
3. Missing edge cases or error handling
4. More efficient or elegant solutions

Create a comprehensive, improved plan that builds upon the previous attempt.
</instruction>
"""

RETRY_WITH_ERROR_PROMPT = """
<instruction>
Based on this query: {query}

And these facts: {fact}

My previous plan was:
{previous_plan}

When this plan was implemented, the following error occurred:
{previous_error}

Please provide an improved plan that specifically addresses this error. Focus on:
1. Fixing the specific issue that caused the error
2. Improving the overall approach if needed
3. Adding better error handling
4. Making the solution more robust

Create a comprehensive, improved plan that avoids the previous error and solves the problem correctly.
</instruction>
"""
