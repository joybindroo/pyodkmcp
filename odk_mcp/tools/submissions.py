"""Submission-related MCP tools."""

import logging
from pathlib import Path
from typing import Literal

import pandas as pd
from mcp.server.mcpserver.exceptions import ToolError

from odk_mcp.core import (
    READ_ONLY,
    WRITE,
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
async def list_submissions(form_id: str, project_id: int | str | None = None) -> list:
    """List submission metadata for a form (instanceId, submitter, reviewState, timestamps).

    To fetch the submission data values, use get_data instead.

    :param form_id: The xmlFormId of the form.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    submissions = await run_blocking(
        c.submissions.list, form_id=form_id, project_id=resolve_project_id(project_id)
    )
    return to_jsonable(submissions)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def get_submission(
    form_id: str, instance_id: str, project_id: int | str | None = None
) -> dict:
    """Read metadata for a single submission.

    :param form_id: The xmlFormId of the form.
    :param instance_id: The instanceId of the submission.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    submission = await run_blocking(
        c.submissions.get,
        instance_id=instance_id,
        form_id=form_id,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(submission)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def get_data(
    form_id: str,
    project_id: int | str | None = None,
    filter: str | None = None,
    top: int | None = None,
    skip: int | None = None,
    select: str | None = None,
    expand: str | None = None,
    count: bool | None = None,
    wkt: bool | None = None,
) -> list:
    """Fetch submission data for a form and sync it into the local SQLite database.

    The fetched rows are stored (flattened) in the table data_pid_<project_id>__fid_<form_id>,
    replacing any previous contents, and the sync timestamp is recorded in table_log.
    Returns the first 50 rows for a preview; query the full table with the pyMCP server.
    OData parameters (filter, top, skip, select, expand, count, wkt) restrict what is
    fetched and therefore what is synced.

    :param form_id: The xmlFormId of the form.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param filter: OData $filter, e.g. "reviewState eq 'approved'" (fields: submitterId,
        createdAt, updatedAt, reviewState; functions now, year, month, day, ...).
    :param top: Only fetch up to this many rows.
    :param skip: Skip this many rows.
    :param select: Comma-separated OData $select of fields to return.
    :param expand: OData $expand; use "*" to expand all repetitions.
    :param count: If True, include the total row count as @odata.count in the response.
    :param wkt: If True, return geospatial data as WKT strings instead of GeoJSON.
    """
    c = require_client()
    pid = resolve_project_id(project_id)
    response = await run_blocking(
        c.submissions.get_table,
        form_id=form_id,
        project_id=pid,
        skip=skip,
        top=top,
        count=count,
        wkt=wkt,
        filter=filter,
        expand=expand,
        select=select,
    )
    data = response.get("value", [])
    if not data:
        raise ToolError("No submissions found for this form.")
    df = pd.json_normalize(data)
    table_name = f"data_pid_{pid}__fid_{sanitize_identifier(form_id)}"
    await run_blocking(sync_table, df, table_name)
    logger.info(f"Synced {len(df)} records to table {table_name}.")
    return df_preview(df)


@mcp.tool(annotations=WRITE)
@tool_errors
async def create_submission(
    form_id: str,
    xml: str,
    project_id: int | str | None = None,
    device_id: str | None = None,
    attachment_paths: list[str] | None = None,
) -> dict:
    """Write: Create a submission from XML, with optional attachment files.

    The XML must include a meta/instanceID element (for example:
    <data id="my_form" version="v1"><meta><instanceID>uuid:...</instanceID></meta>...</data>).
    Attachment file names must match file name references in the XML.

    :param form_id: The xmlFormId of the form.
    :param xml: The submission XML content.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param device_id: Optional deviceID to associate with the submission.
    :param attachment_paths: Local paths of attachment files to upload.
    """
    c = require_client()
    attachments = [Path(p) for p in attachment_paths] if attachment_paths else None
    submission = await run_blocking(
        c.submissions.create,
        xml=xml,
        form_id=form_id,
        project_id=resolve_project_id(project_id),
        device_id=device_id,
        attachments=attachments,
    )
    return to_jsonable(submission)


@mcp.tool(annotations=WRITE)
@tool_errors
async def edit_submission(
    form_id: str,
    instance_id: str,
    xml: str,
    project_id: int | str | None = None,
    comment: str | None = None,
) -> dict:
    """Write: Edit a submission by uploading a new version of its XML, with an optional comment.

    The new XML must include meta/deprecatedID (the previous instanceID) and a new
    meta/instanceID. The instance_id argument is the submission's original instanceId.

    :param form_id: The xmlFormId of the form.
    :param instance_id: The submission's instanceId.
    :param xml: The edited submission XML content.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param comment: Optional comment to attach to the edit.
    """
    c = require_client()
    pid = resolve_project_id(project_id)
    await run_blocking(
        c.submissions.edit,
        instance_id=instance_id,
        xml=xml,
        form_id=form_id,
        project_id=pid,
        comment=comment,
    )
    submission = await run_blocking(
        c.submissions.get, instance_id=instance_id, form_id=form_id, project_id=pid
    )
    return to_jsonable(submission)


@mcp.tool(annotations=WRITE)
@tool_errors
async def review_submission(
    form_id: str,
    instance_id: str,
    review_state: Literal["approved", "hasIssues", "rejected"],
    project_id: int | str | None = None,
    comment: str | None = None,
) -> dict:
    """Write: Set the review state of a submission, with an optional comment.

    :param form_id: The xmlFormId of the form.
    :param instance_id: The submission's instanceId.
    :param review_state: The new review state.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param comment: Optional comment to attach to the review.
    """
    c = require_client()
    pid = resolve_project_id(project_id)
    await run_blocking(
        c.submissions.review,
        instance_id=instance_id,
        review_state=review_state,
        form_id=form_id,
        project_id=pid,
        comment=comment,
    )
    submission = await run_blocking(
        c.submissions.get, instance_id=instance_id, form_id=form_id, project_id=pid
    )
    return to_jsonable(submission)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def list_submission_comments(
    form_id: str, instance_id: str, project_id: int | str | None = None
) -> list:
    """List the comments on a submission.

    :param form_id: The xmlFormId of the form.
    :param instance_id: The submission's instanceId.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    comments = await run_blocking(
        c.submissions.list_comments,
        instance_id=instance_id,
        form_id=form_id,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(list(comments))


@mcp.tool(annotations=WRITE)
@tool_errors
async def add_submission_comment(
    form_id: str, instance_id: str, comment: str, project_id: int | str | None = None
) -> dict:
    """Write: Add a comment to a submission.

    :param form_id: The xmlFormId of the form.
    :param instance_id: The submission's instanceId.
    :param comment: The comment text.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    result = await run_blocking(
        c.submissions.add_comment,
        instance_id=instance_id,
        comment=comment,
        form_id=form_id,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(result)
