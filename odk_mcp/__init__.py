"""ODK MCP server package."""

from odk_mcp.core import mcp
from odk_mcp import tools  # noqa: F401  # Importing registers all tools on the server.

__all__ = ["mcp"]
