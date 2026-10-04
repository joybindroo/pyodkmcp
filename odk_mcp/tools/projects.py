"""Project-related MCP tools."""

from odk_mcp.core import (
    READ_ONLY,
    WRITE,
    mcp,
    require_client,
    resolve_project_id,
    run_blocking,
    to_jsonable,
    tool_errors,
)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def list_projects() -> list:
    """List all ODK Central projects available to the configured user.

    Use the returned project_id with the other tools in this server.
    """
    c = require_client()
    projects = await run_blocking(c.projects.list)
    return [{"project_id": str(p.id), "name": p.name} for p in projects]


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def get_project(project_id: int | str | None = None) -> dict:
    """Read full details of a single project (name, description, form/app user counts, timestamps).

    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    project = await run_blocking(c.projects.get, resolve_project_id(project_id))
    return to_jsonable(project)


@mcp.tool(annotations=WRITE)
@tool_errors
async def create_app_users(
    display_names: list[str],
    project_id: int | str | None = None,
    form_ids: list[str] | None = None,
) -> list:
    """Write: Create app users in a project, optionally assigning forms to them.

    Creates one app user per display name; existing users with the same display name and
    a token are skipped. Use the returned tokens to provision ODK Collect devices.

    :param display_names: Friendly nicknames for the app users to create.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param form_ids: Optional xmlFormIds of forms to assign to each new app user.
    """
    c = require_client()
    users = await run_blocking(
        c.projects.create_app_users,
        display_names=display_names,
        forms=form_ids,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(list(users))
