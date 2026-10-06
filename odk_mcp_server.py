"""ODK MCP Server entry point.

Exposes ODK Central projects, forms, submissions, entities, and entity lists - plus a
raw Central API bridge - as MCP tools, backed by PyODK and a local SQLite database.

By default the server runs in stdio mode (the standard MCP transport). Use
--transport sse to expose the server over HTTP so any MCP client supporting the
SSE transport can connect without launching a subprocess.
"""

import argparse

from odk_mcp import mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="ODK MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for sse/streamable-http transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for sse/streamable-http transports (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport=args.transport,
            host=args.host,
            port=args.port,
        )


if __name__ == "__main__":
    main()
