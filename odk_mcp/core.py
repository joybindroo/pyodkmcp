"""Shared configuration, PyODK client, and helpers for the ODK MCP server."""

import asyncio
import datetime
import functools
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel
from pyodk.client import Client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("odk-mcp")

mcp = MCPServer(
    name="odk-mcp",
    instructions=(
        "ODK Central ingestion and management server. Discover projects with "
        "list_projects, discover forms with list_forms, then sync submission data with "
        "get_data (or entity data with get_entity_data) into the local SQLite database "
        "and query the synced tables with the pyMCP database server. Tools whose "
        "description starts with 'Write:' modify data in ODK Central."
    ),
)

#: Tool annotations for read-only tools.
READ_ONLY = ToolAnnotations(readOnlyHint=True)
#: Tool annotations for tools that modify data in ODK Central.
WRITE = ToolAnnotations(readOnlyHint=False)
#: Tool annotations for destructive tools that delete data in ODK Central.
WRITE_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)

DB_PATH = os.getenv("ODK_MCP_DB_PATH", "odk_mcp_server.db")
PROJECT_DIR = Path(__file__).resolve().parent.parent
PROJECT_CONFIG_PATH = PROJECT_DIR / "pyodk_config.toml"
logger.info(f"Initializing ODK MCP Server. Database path: {DB_PATH}")

config_path = None
config_source = "~/.pyodk_config.toml"
if os.environ.get("PYODK_CONFIG_FILE"):
    config_source = os.environ["PYODK_CONFIG_FILE"]
elif PROJECT_CONFIG_PATH.is_file():
    config_path = PROJECT_CONFIG_PATH
    config_source = str(PROJECT_CONFIG_PATH)

try:
    client = Client(config_path=config_path)
    logger.info(f"PyODK Client initialized successfully (config: {config_source}).")
except Exception as e:
    logger.error(f"Failed to initialize PyODK Client (config: {config_source}): {e}")
    client = None


def require_client() -> Client:
    """Return the PyODK client, or raise a clear error if it isn't configured."""
    if client is None:
        raise ToolError(
            "ODK Client not initialized. Check your PyODK configuration (credentials "
            "and base_url) in ~/.pyodk_config.toml or the PYODK_CONFIG_FILE env var."
        )
    return client


def resolve_project_id(project_id: int | str | None) -> int:
    """Resolve the effective project id, falling back to the PyODK default."""
    c = require_client()
    pid = project_id.strip() if isinstance(project_id, str) else project_id
    if isinstance(pid, str) and pid.isdigit():
        pid = int(pid)
    if pid is None:
        pid = c.project_id
    if pid is None:
        raise ToolError(
            "project_id is required because no default_project_id is configured."
        )
    return pid


def get_db_connection() -> sqlite3.Connection:
    """Return a sqlite3 connection to the configured database."""
    return sqlite3.connect(DB_PATH)


async def run_blocking(fn, *args, **kwargs) -> Any:
    """Run a blocking function in a worker thread so the server stays responsive."""
    return await asyncio.to_thread(functools.partial(fn, *args, **kwargs))


def to_jsonable(obj: Any) -> Any:
    """Recursively convert PyODK models and other objects to JSON-safe structures."""
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    return obj


def sanitize_identifier(name: str) -> str:
    """Make a name safe for use in a SQLite table name."""
    return name.replace(" ", "_").replace("-", "_")


def df_preview(df: pd.DataFrame, limit: int = 50) -> list[dict]:
    """Return up to limit rows as JSON-safe records (NaN -> null, datetimes -> ISO)."""
    return json.loads(df.head(limit).to_json(orient="records", date_format="iso"))


def sync_table(df: pd.DataFrame, table_name: str) -> None:
    """Replace a SQLite table with the given DataFrame and log the sync timestamp."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        log_df = pd.DataFrame({"table": [table_name], "update_ts": [now]})
        log_df.to_sql("table_log", conn, if_exists="append", index=False)


def tool_errors(fn):
    """Decorator: log exceptions and re-raise them as MCP tool errors."""

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except ToolError:
            raise
        except Exception as e:
            logger.exception(f"Tool '{fn.__name__}' failed: {e}")
            raise ToolError(f"{type(e).__name__}: {e}") from e

    return wrapper
