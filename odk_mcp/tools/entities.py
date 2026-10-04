"""Entity MCP tools."""

import logging

import pandas as pd
from mcp.server.mcpserver.exceptions import ToolError

from odk_mcp.core import (
    READ_ONLY,
    WRITE,
    WRITE_DESTRUCTIVE,
    df_preview,
    mcp,
    require_client,
    resolve_project_id,
    run_blocking,
    sanitize_identifier,
    sync_table,
    to_jsonable,
    tool_errors,
)

logger = logging.getLogger("odk-mcp")


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def list_entities(
    entity_list_name: str, project_id: int | str | None = None
) -> list:
    """List entity metadata in an entity list (uuid, timestamps, current version with label and data).

    To fetch the full entity data table, use get_entity_data instead.

    :param entity_list_name: The name of the entity list (dataset).
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    entities = await run_blocking(
        c.entities.list,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(entities)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def get_entity_data(
    entity_list_name: str,
    project_id: int | str | None = None,
    filter: str | None = None,
    top: int | None = None,
    skip: int | None = None,
    select: str | None = None,
    count: bool | None = None,
) -> list:
    """Fetch entity data from an entity list and sync it into the local SQLite database.

    The fetched rows are stored (flattened) in the table entity_pid_<project_id>__el_<entity_list_name>,
    replacing any previous contents, and the sync timestamp is recorded in table_log.
    Returns the first 50 rows for a preview; query the full table with the pyMCP server.
    OData parameters (filter, top, skip, select, count) restrict what is fetched and
    therefore what is synced.

    :param entity_list_name: The name of the entity list (dataset).
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param filter: OData $filter expression over the entity fields.
    :param top: Only fetch up to this many rows.
    :param skip: Skip this many rows.
    :param select: Comma-separated OData $select of fields to return.
    :param count: If True, include the total row count as @odata.count in the response.
    """
    c = require_client()
    pid = resolve_project_id(project_id)
    response = await run_blocking(
        c.entities.get_table,
        entity_list_name=entity_list_name,
        project_id=pid,
        skip=skip,
        top=top,
        count=count,
        filter=filter,
        select=select,
    )
    data = response.get("value", [])
    if not data:
        raise ToolError("No entities found in this entity list.")
    df = pd.json_normalize(data)
    table_name = f"entity_pid_{pid}__el_{sanitize_identifier(entity_list_name)}"
    await run_blocking(sync_table, df, table_name)
    logger.info(f"Synced {len(df)} entity records to table {table_name}.")
    return df_preview(df)


@mcp.tool(annotations=WRITE)
@tool_errors
async def create_entities(
    entity_list_name: str,
    data: list[dict],
    project_id: int | str | None = None,
    create_source: str | None = None,
) -> dict:
    """Write: Create one or more entities in a single request.

    Each item in data must include a "label" key; other keys become entity properties and
    must already exist on the entity list (use add_entity_list_property to create them, or
    merge_entities to add them automatically).

    :param entity_list_name: The name of the entity list (dataset).
    :param data: List of entities to create, e.g. [{"label": "Sydney", "state": "NSW"}].
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param create_source: Optional label for the source of these entities (e.g. a file name).
    """
    c = require_client()
    success = await run_blocking(
        c.entities.create_many,
        data=data,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
        create_source=create_source,
    )
    return {"success": success}


@mcp.tool(annotations=WRITE)
@tool_errors
async def update_entity(
    uuid: str,
    entity_list_name: str,
    project_id: int | str | None = None,
    label: str | None = None,
    data: dict | None = None,
    base_version: int | None = None,
    force: bool | None = None,
) -> dict:
    """Write: Update an entity's label and/or data.

    Specify exactly one of base_version (the entity's current version, visible in
    get_entity_data / list_entities) or force=True (overwrite regardless of conflicts).

    :param uuid: The unique identifier of the entity.
    :param entity_list_name: The name of the entity list (dataset).
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param label: New label for the entity.
    :param data: New data for the entity (replaces the given properties).
    :param base_version: The expected current version of the entity on the server.
    :param force: If True, update regardless of the entity's current state.
    """
    c = require_client()
    entity = await run_blocking(
        c.entities.update,
        uuid=uuid,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
        label=label,
        data=data,
        force=force,
        base_version=base_version,
    )
    return to_jsonable(entity)


@mcp.tool(annotations=WRITE_DESTRUCTIVE)
@tool_errors
async def delete_entity(
    uuid: str, entity_list_name: str, project_id: int | str | None = None
) -> dict:
    """Write: Permanently delete an entity from an entity list.

    :param uuid: The unique identifier of the entity.
    :param entity_list_name: The name of the entity list (dataset).
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    success = await run_blocking(
        c.entities.delete,
        uuid=uuid,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
    )
    return {"success": success}


@mcp.tool(annotations=WRITE)
@tool_errors
async def merge_entities(
    entity_list_name: str,
    data: list[dict],
    project_id: int | str | None = None,
    match_keys: list[str] | None = None,
    add_new_properties: bool = True,
    update_matched: bool = True,
    delete_not_matched: bool = False,
    source_label_key: str = "label",
    create_source: str | None = None,
) -> dict:
    """Write: Create, update, and optionally delete entities so Central matches the given data.

    Entities are matched by match_keys (default: ["label"]). Missing entity list properties
    are added automatically unless add_new_properties is False. Set delete_not_matched=True
    to delete entities in Central that are absent from data (destructive, off by default).
    Large merges can be slow: each update/delete is a separate API request.

    :param entity_list_name: The name of the entity list (dataset).
    :param data: List of entities, e.g. [{"label": "Sydney", "state": "NSW"}].
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param match_keys: Keys used to match rows between data and Central (default ["label"]).
    :param add_new_properties: Add any entity list properties from data that don't exist yet.
    :param update_matched: Update entities in Central that match data but differ.
    :param delete_not_matched: Delete entities in Central that are not present in data.
    :param source_label_key: Key in data to use as the label (target key is always "label").
    :param create_source: Optional label for the source of inserted entities.
    """
    c = require_client()
    actions = await run_blocking(
        c.entities.merge,
        data=data,
        entity_list_name=entity_list_name,
        project_id=resolve_project_id(project_id),
        match_keys=match_keys,
        add_new_properties=add_new_properties,
        update_matched=update_matched,
        delete_not_matched=delete_not_matched,
        source_label_key=source_label_key,
        create_source=create_source,
    )
    return {
        "inserted": len(actions.to_insert),
        "updated": len(actions.to_update) if update_matched else 0,
        "deleted": len(actions.to_delete) if delete_not_matched else 0,
        "properties_added": sorted(actions.keys_difference) if add_new_properties else [],
        "match_keys": actions.match_keys,
    }
