from typing import Any, Dict, List, Callable
from app.core.openapi_parser import ParsedEndpoint, OpenAPIParser


class OpenAPIToolBuilder:
	def __init__(self, openapi_spec: Dict[str, Any], api_key: str, base_url: str | None = None):
		self.openapi_spec = openapi_spec
		self.api_key = api_key
		self.base_url = base_url

	def build_all_tools(self) -> List[Callable]:
		parser = OpenAPIParser(self.openapi_spec)
		endpoints = parser.parse_endpoints()
		tools: List[Callable] = []
		for ep in endpoints:
			def _tool_factory(e: ParsedEndpoint):
				def tool(**kwargs):
					"""OpenAPI endpoint tool."""
					return {"endpoint": e.operation_id, "kwargs": kwargs}
				tool.__name__ = e.operation_id
				tool.__doc__ = e.description or e.summary or ""
				return tool
			tools.append(_tool_factory(ep))
		return tools





