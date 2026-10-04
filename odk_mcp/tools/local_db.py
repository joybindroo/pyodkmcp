"""Local SQLite database utility tools."""

from odk_mcp.core import (
    READ_ONLY,
    get_db_connection,
    mcp,
    run_blocking,
    tool_errors,
)


def _read_table_log() -> list[dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='table_log'"
        )
        if cursor.fetchone() is None:
            return []
        cursor.execute(
            'SELECT "table", update_ts FROM table_log ORDER BY update_ts DESC'
        )
        return [{"table_name": row[0], "update_ts": row[1]} for row in cursor.fetchall()]


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def list_synced_tables() -> list:
    """List tables synced into the local SQLite database, newest first, with sync timestamps.

    Use this to check how fresh a synced table is before analysis with the pyMCP server.
    """
    return await run_blocking(_read_table_log)
