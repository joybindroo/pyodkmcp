"""Generic ODK Central API request bridge."""

import logging
from typing import Any, Literal

from mcp.server.mcpserver.exceptions import ToolError

from odk_mcp.core import WRITE, mcp, require_client, run_blocking, tool_errors

logger = logging.getLogger("odk-mcp")

MAX_RESPONSE_CHARS = 20000


@mcp.tool(annotations=WRITE)
@tool_errors
async def central_api_request(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
) -> Any:
    """Write: Call any ODK Central API endpoint directly (raw HTTP request).

    Use this for Central API functionality not covered by the dedicated tools, e.g. form
    drafts, form assignments, project roles, or user management. The path is relative to
    the Central API base URL, e.g. "projects/1/forms", "projects/1/forms/my_form/draft",
    or "v1/projects" is not needed: the API version prefix is added automatically.

    GET and other read requests are safe; POST/PUT/PATCH/DELETE modify data in Central.

    :param method: HTTP method.
    :param path: API path relative to the API base URL (e.g. "projects/1/forms").
    :param params: Optional query parameters, e.g. {"$top": 10}.
    :param json_body: Optional JSON body for POST/PUT/PATCH requests.
    """
    clean_path = path.strip().lstrip("/")
    if "://" in path:
        raise ToolError(
            "path must be relative to the Central API base URL (no scheme or host), "
            "e.g. 'projects/1/forms'."
        )
    if not clean_path or ".." in clean_path:
        raise ToolError(
            "path must be a non-empty relative API path, e.g. 'projects/1/forms'."
        )
    c = require_client()
    logger.info(f"Central API request: {method} {clean_path}")

    def _request():
        verb = getattr(c, method.lower())
        response = verb(clean_path, params=params or None, json=json_body or None)
        response.raise_for_status()
        return response

    response = await run_blocking(_request)
    content_type = response.headers.get("Content-Type", "")
    if "json" in content_type.lower():
        try:
            return response.json()
        except ValueError:
            pass
    text = response.text
    return {
        "status_code": response.status_code,
        "content_type": content_type,
        "text": text[:MAX_RESPONSE_CHARS],
        "truncated": len(text) > MAX_RESPONSE_CHARS,
    }
