"""Entity list (dataset) MCP tools."""

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
async def list_entity_lists(project_id: int | str | None = None) -> list:
    """List all entity lists (datasets) in a project with their properties.

    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    entity_lists = await run_blocking(
        c.entity_lists.list, project_id=resolve_project_id(project_id)
    )
    return to_jsonable(entity_lists)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def get_entity_list(
    entity_list_name: str, project_id: int | str | None = None
) -> dict:
    """Read details of a single entity list, including its properties.

    :param entity_list_name: The name of the entity list (dataset).
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    entity_list = await run_blocking(
        c.entity_lists.get,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(entity_list)


@mcp.tool(annotations=WRITE)
@tool_errors
async def create_entity_list(
    entity_list_name: str,
    project_id: int | str | None = None,
    approval_required: bool = False,
) -> dict:
    """Write: Create an entity list (dataset) in a project.

    :param entity_list_name: The name of the entity list (dataset) to create.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param approval_required: If True, entities are created when submissions are marked
        approved in Central; if False, as soon as submissions are received.
    """
    c = require_client()
    entity_list = await run_blocking(
        c.entity_lists.create,
        approval_required=approval_required,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(entity_list)


@mcp.tool(annotations=WRITE)
@tool_errors
async def add_entity_list_property(
    entity_list_name: str,
    property_name: str,
    project_id: int | str | None = None,
) -> dict:
    """Write: Add a property to an entity list.

    Property names follow form field naming rules (valid XML identifiers) and cannot be
    "name", "label", or start with "__".

    :param entity_list_name: The name of the entity list (dataset).
    :param property_name: The name of the property to add.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    success = await run_blocking(
        c.entity_lists.add_property,
        name=property_name,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
    )
    return {"success": success}
