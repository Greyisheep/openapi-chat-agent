import httpx
import re
import yaml
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse


@dataclass
class ParsedEndpoint:
	operation_id: str
	method: str
	path: str
	summary: Optional[str]
	description: Optional[str]


class OpenAPIParser:
	def __init__(self, spec: Dict[str, Any]):
		self.spec = spec
		servers = spec.get("servers", [])
		self.base_url = servers[0]["url"] if servers else ""

	def parse_endpoints(self) -> List[ParsedEndpoint]:
		endpoints: List[ParsedEndpoint] = []
		paths = self.spec.get("paths", {})
		for path, ops in paths.items():
			for method, op in ops.items():
				if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
					continue
				operation_id = op.get("operationId") or f"{method.lower()}_{path.strip('/').replace('/', '_') or 'root'}"
				endpoints.append(ParsedEndpoint(
					operation_id=operation_id,
					method=method.upper(),
					path=path,
					summary=op.get("summary"),
					description=(op.get("description") or op.get("summary"))
				))
		return endpoints


async def get_spec_from_url(url: str) -> Dict[str, Any]:
    """
    Fetches an OpenAPI/Swagger specification from a URL.
    Handles both direct links to JSON/YAML files and links to Swagger UI HTML pages.
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            
            # Try to parse as JSON or YAML directly
            if "json" in content_type:
                return response.json()
            if "yaml" in content_type or "yml" in content_type:
                return yaml.safe_load(response.text)
            
            # If it's HTML, assume it's a Swagger UI page and find the spec URL
            if "html" in content_type:
                html_content = response.text
                # Regex to find common patterns for spec URLs in Swagger UI initializers
                spec_url_match = re.search(
                    r"""
                        url:\s*["']([^"']+\.(?:json|yaml|yml))["']|  # Matches url: "..."
                        urls:\s*\[\s*\{\s*url:\s*["']([^"']+)["']    # Matches urls: [{ url: "..." ... }]
                    """,
                    html_content,
                    re.VERBOSE
                )
                
                if spec_url_match:
                    # The regex has two capture groups, one will be None
                    spec_path = spec_url_match.group(1) or spec_url_match.group(2)
                    if spec_path:
                        # Join with base URL in case it's a relative path
                        spec_url = urljoin(str(response.url), spec_path)
                        
                        # Fetch the actual spec file
                        spec_response = await client.get(spec_url)
                        spec_response.raise_for_status()
                        
                        if ".yaml" in spec_url or ".yml" in spec_url:
                            return yaml.safe_load(spec_response.text)
                        else:
                            return spec_response.json()
                
                # Fallback for some Swagger pages that define the spec inline
                inline_spec_match = re.search(
                    r'spec:\s*(\{.*\}|\S.*),\s*$', 
                    html_content, 
                    re.DOTALL | re.MULTILINE
                )
                if inline_spec_match:
                    spec_str = inline_spec_match.group(1).strip()
                    try:
                        return json.loads(spec_str)
                    except json.JSONDecodeError:
                        pass  # It might be YAML or just a JS object literal

            # If all else fails, try common relative paths
            for path in ["/openapi.json", "/swagger.json", "/api-docs", "/v2/api-docs", "/v3/api-docs"]:
                try:
                    spec_url = urljoin(url, path)
                    spec_response = await client.get(spec_url)
                    if spec_response.status_code == 200:
                        return spec_response.json()
                except (httpx.RequestError, ValueError):
                    continue

            raise ValueError("Could not find or parse OpenAPI specification from the provided URL.")

        except httpx.RequestError as e:
            raise ValueError(f"Failed to fetch from URL: {e}")
        except (ValueError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to parse OpenAPI specification: {e}")



