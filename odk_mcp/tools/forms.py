"""Form-related MCP tools."""

from pathlib import Path

from mcp.server.mcpserver.exceptions import ToolError

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


def _form_definition(
    definition_path: str | None, definition_xml: str | None
) -> Path | str:
    if (definition_path is None) == (definition_xml is None):
        raise ToolError("Specify exactly one of definition_path or definition_xml.")
    if definition_path is not None:
        return Path(definition_path)
    return definition_xml


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def list_forms(project_id: int | str | None = None) -> list:
    """List all forms in a project with their metadata (xmlFormId, name, version, state, timestamps).

    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    forms = await run_blocking(c.forms.list, project_id=resolve_project_id(project_id))
    return to_jsonable(forms)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def get_form(form_id: str, project_id: int | str | None = None) -> dict:
    """Read metadata for a single form.

    :param form_id: The xmlFormId of the form.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    form = await run_blocking(
        c.forms.get, form_id=form_id, project_id=resolve_project_id(project_id)
    )
    return to_jsonable(form)


@mcp.tool(annotations=READ_ONLY)
@tool_errors
async def get_form_xml(form_id: str, project_id: int | str | None = None) -> str:
    """Read the XForms XML definition of a form.

    :param form_id: The xmlFormId of the form.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    """
    c = require_client()
    xml = await run_blocking(
        c.forms.get_xml, form_id=form_id, project_id=resolve_project_id(project_id)
    )
    return xml


@mcp.tool(annotations=WRITE)
@tool_errors
async def create_form(
    project_id: int | str | None = None,
    form_id: str | None = None,
    definition_path: str | None = None,
    definition_xml: str | None = None,
    attachment_paths: list[str] | None = None,
    ignore_warnings: bool = True,
) -> dict:
    """Write: Create a new form in a project (upload the definition, then publish it).

    Provide exactly one definition: definition_path (a local .xlsx, .xls, or .xml file) or
    definition_xml (raw XForm XML content). Attachments are local file paths matched by
    file name to media/questions in the form.

    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param form_id: Optional desired xmlFormId; otherwise derived from the definition.
    :param definition_path: Path to the form definition file on this machine.
    :param definition_xml: Raw XForm XML content.
    :param attachment_paths: Local paths of form attachment files to upload.
    :param ignore_warnings: If True, proceed if the XLSForm has warnings.
    """
    c = require_client()
    definition = _form_definition(definition_path, definition_xml)
    attachments = [Path(p) for p in attachment_paths] if attachment_paths else None
    form = await run_blocking(
        c.forms.create,
        definition=definition,
        attachments=attachments,
        ignore_warnings=ignore_warnings,
        form_id=form_id,
        project_id=resolve_project_id(project_id),
    )
    return to_jsonable(form)


@mcp.tool(annotations=WRITE)
@tool_errors
async def update_form(
    form_id: str,
    project_id: int | str | None = None,
    definition_path: str | None = None,
    definition_xml: str | None = None,
    attachment_paths: list[str] | None = None,
    new_version: str | None = None,
) -> dict:
    """Write: Update a form by creating and publishing a new version (new definition and/or attachments).

    Provide a new definition (definition_path or definition_xml) and/or attachments. If a
    definition is provided it must contain the new version string. If only attachments are
    provided, the version defaults to the current timestamp unless new_version is set.

    :param form_id: The xmlFormId of the form to update.
    :param project_id: The id of the project. Defaults to the PyODK default_project_id.
    :param definition_path: Path to the new form definition file on this machine.
    :param definition_xml: Raw XForm XML content of the new version.
    :param attachment_paths: Local paths of form attachment files to upload.
    :param new_version: Version string for an attachments-only update.
    """
    c = require_client()
    definition = None
    if definition_path is not None or definition_xml is not None:
        definition = _form_definition(definition_path, definition_xml)
    attachments = [Path(p) for p in attachment_paths] if attachment_paths else None
    if definition is None and attachments is None:
        raise ToolError("Must specify a form definition and/or attachments to update.")
    if definition is not None and new_version is not None:
        raise ToolError(
            "new_version must not be used with a form definition; set the new version "
            "inside the definition instead."
        )
    version_updater = (lambda _: new_version) if new_version is not None else None
    pid = resolve_project_id(project_id)
    await run_blocking(
        c.forms.update,
        form_id=form_id,
        project_id=pid,
        definition=definition,
        attachments=attachments,
        version_updater=version_updater,
    )
    form = await run_blocking(c.forms.get, form_id=form_id, project_id=pid)
    return to_jsonable(form)
