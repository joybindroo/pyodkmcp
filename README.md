# 🚀 Python MCP Server for ODK

A Model Context Protocol (MCP) Server for ODK Central, enabling AI agents to interact with your data collection projects, forms, submissions, entities, and app users using the powerful [PyODK](https://github.com/getodk/pyodk) Python library.

This server acts as the **Ingestion Layer**, fetching data from ODK Central and storing it in a local SQLite database, which is then queried by a dedicated **Database MCP Server** (like [pyMCP](https://github.com/joybindroo/pyMCP)) for high-performance analysis. It also exposes the full PyODK management API plus a raw HTTP bridge to any [ODK Central API](https://docs.getodk.org/central-api) endpoint.

---

## 🛠️ Tools and Dual-Server Workflow

### 1. ODK MCP Server

#### Read tools (safe, no changes to Central)

| Tool | Description |
|---|---|
| `list_projects()` | List all projects available to the configured user. |
| `get_project(project_id)` | Full details of one project. |
| `list_forms(project_id)` | List forms in a project. |
| `get_form(project_id, form_id)` | Form metadata. |
| `get_form_xml(project_id, form_id)` | The XForms XML definition of a form. |
| `list_submissions(project_id, form_id)` | Submission metadata (no data values). |
| `get_submission(project_id, form_id, instance_id)` | One submission's metadata. |
| `get_data(project_id, form_id, ...)` | Fetch submission data (with optional OData filter/top/skip/select/expand/count/wkt), flatten it with pandas, and store it in a local SQLite table. |
| `list_submission_comments(project_id, form_id, instance_id)` | Comments on a submission. |
| `list_entity_lists(project_id)` | Entity lists (datasets) in a project, with properties. |
| `get_entity_list(project_id, entity_list_name)` | Details of one entity list. |
| `list_entities(project_id, entity_list_name)` | Entity metadata in an entity list. |
| `get_entity_data(project_id, entity_list_name, ...)` | Fetch entity data (with optional OData params) and store it in a local SQLite table. |
| `list_synced_tables()` | Tables synced into the local SQLite database, with sync timestamps. |

#### Write tools (modify data in Central)

| Tool | Description |
|---|---|
| `create_app_users(display_names, project_id, form_ids)` | Create app users, optionally assigning forms. |
| `create_form(...)` / `update_form(...)` | Create a form from an XLSForm/XML file or raw XML; publish new versions. |
| `create_submission(...)` / `edit_submission(...)` | Create a submission from XML (with optional attachments); edit an existing one. |
| `review_submission(..., review_state, comment)` | Set a submission's review state (approved/hasIssues/rejected). |
| `add_submission_comment(...)` | Comment on a submission. |
| `create_entity_list(...)` / `add_entity_list_property(...)` | Create datasets and their properties. |
| `create_entities(...)` / `update_entity(...)` / `delete_entity(...)` / `merge_entities(...)` | Create, update, delete, or bulk merge entities. |
| `central_api_request(method, path, ...)` | Raw bridge: call any Central API endpoint not covered by the tools above (form drafts, assignments, admin, ...). |

**How syncing works**: `get_data` flattens nested submission JSON into a tabular format and stores it in a SQLite table named `data_pid_{project_id}__fid_{form_id}` (replacing any previous contents). `get_entity_data` stores entity data in `entity_pid_{project_id}__el_{entity_list_name}`. Both log the sync timestamp in the `table_log` table and return a preview of up to 50 rows.

### 2. Database MCP Server (The Analyst)
Once `get_data` (or `get_entity_data`) has synced the information, the AI agent transitions to the Database MCP Server (pyMCP) to perform natural language SQL queries against the local SQLite file.

---

## 🪴 Installation & Setup

### 1. Prerequisites
- Python 3.12+
- A configured PyODK environment (see [PyODK Configuration](https://github.com/getodk/pyodk#configure)).

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/joybindroo/pyodkmcp.git
cd pyodkmcp

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
# venv\Scripts\activate   # Windows

# Install dependencies (PyODK 1.3.0+, MCP SDK, pandas)
pip install -r requirements.txt
```

### 3. Configuration
The server uses an environment variable to determine where to store the SQLite database.
- **Variable**: `ODK_MCP_DB_PATH`
- **Default**: `odk_mcp_server.db` (local directory)

Credentials are read from `pyodk_config.toml` in the project root when it exists (copy `pyodk_config.toml.template` and fill in real values). Otherwise the standard PyODK resolution is used: the `PYODK_CONFIG_FILE` environment variable, then `~/.pyodk_config.toml`. Setting `PYODK_CONFIG_FILE` always takes precedence over the project-level file.

---

## 🔌 MCP Client Configuration

Example configuration for Claude Desktop or other MCP clients (point `command` at the project venv Python):

```json
{
  "odk_mcp_server": {
    "command": "/path/to/pyodkmcp/venv/bin/python",
    "args": ["/path/to/pyodkmcp/odk_mcp_server.py"],
    "env": {
      "ODK_MCP_DB_PATH": "/path/to/odk_mcp_server.db"
    }
  },
  "odk_mcp_sqlite_data": {
    "command": "python",
    "args": [
      "/path/to/pymcp/db_mcp_server.py",
      "sqlite:// /path/to/odk_mcp_server.db"
    ],
    "env": {
      "PYTHONPATH": "/path/to/pymcp"
    }
  }
}
```

---

## ⚠️ Notes

- Write tools change data in ODK Central. The most destructive operations (`delete_entity`, `merge_entities(delete_not_matched=True)`, non-GET `central_api_request` calls) should be used deliberately.
- Tool failures are surfaced as MCP tool errors (`isError`), e.g. `ODK Client not initialized.` when the PyODK configuration is missing, or `No submissions found for this form.` for empty forms.

## 🛣️ Roadmap
- [ ] **Data Export**: Export synced tables to CSV/Excel.
- [ ] **Async DB**: Migration to `aiosqlite` for non-blocking I/O.
- [ ] **Version Monitoring**: Integration with `PyXComparer` to detect schema changes between syncs.

## 🤝 Community
If you find this server useful, please consider giving the repository a star!
