from research_agent.tools.base import BaseTool, ToolResult
from research_agent.tools.web_search import WebSearchTool
from research_agent.tools.fetch_url import FetchUrlTool
from research_agent.tools.python_sandbox import PythonSandboxTool
from research_agent.tools.local_docs import LocalDocsTool
from research_agent.tools.elastic_rag import ElasticRagTool

TOOL_REGISTRY: dict[str, type[BaseTool]] = {
    "web_search": WebSearchTool,
    "fetch_url": FetchUrlTool,
    "python_sandbox": PythonSandboxTool,
    "local_docs": LocalDocsTool,
    "elastic_rag": ElasticRagTool,
}

__all__ = [
    "BaseTool",
    "ToolResult",
    "WebSearchTool",
    "FetchUrlTool",
    "PythonSandboxTool",
    "LocalDocsTool",
    "ElasticRagTool",
    "TOOL_REGISTRY",
]
