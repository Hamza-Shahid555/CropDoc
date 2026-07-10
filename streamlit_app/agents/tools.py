"""Aggregates the Tool Agent (internal Python functions) and API Agent
(external HTTP calls) into one registry the Response Agent's function-calling
loop can hand straight to the OpenAI client."""

from . import api_agent, tool_agent

TOOL_SCHEMAS = tool_agent.TOOL_SCHEMAS + api_agent.TOOL_SCHEMAS
TOOL_FUNCTIONS = {**tool_agent.TOOL_FUNCTIONS, **api_agent.TOOL_FUNCTIONS}
