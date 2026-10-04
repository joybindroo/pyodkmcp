"""ODK MCP Server entry point.

Exposes ODK Central projects, forms, submissions, entities, and entity lists - plus a
raw Central API bridge - as MCP tools, backed by PyODK and a local SQLite database.
"""

from odk_mcp import mcp

if __name__ == "__main__":
    mcp.run()
