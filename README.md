# 🚀 Python MCP Server for ODK

A Model Context Protocol (MCP) Server for ODK Central, enabling AI agents to interact with your data collection projects and forms using the powerful [PyODK](https://github.com/getodk/pyodk) Python library. 

This server acts as the **Ingestion Layer**, fetching data from ODK Central and storing it in a local SQLite database, which is then queried by a dedicated **Database MCP Server** (like [pyMCP](https://github.com/joybindroo/pyMCP)) for high-performance analysis.

---

## 🛠️ Tools and Dual-Server Workflow

This setup utilizes two separate, but interconnected, MCP servers to create a robust agentic workflow.

### 1. ODK MCP Server (The Ingestor)
This server handles the communication with the ODK Central API:
- `list_projects()`: Fetches all projects available to the configured user.
- `list_forms(project_id: int)`: Retrieves all forms within a specific project.
- `get_data(project_id_str: str, form_id_str: str)`: 
    - Fetches submission data.
    - Flattens nested JSON into a tabular format using `pandas`.
    - Stores the data in a local SQLite table named `data_pid_{project_id}__fid_{form_id}`.
    - Logs the sync timestamp in the `table_log` table.

### 2. Database MCP Server (The Analyst)
Once `get_data` has synced the information, the AI agent transitions to the Database MCP Server (pyMCP) to perform natural language SQL queries against the local SQLite file.

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

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# venv\\Scripts\\activate # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
The server uses an environment variable to determine where to store the SQLite database.
- **Variable**: `ODK_MCP_DB_PATH`
- **Default**: `odk_mcp_server.db` (local directory)

---

## 🔌 MCP Client Configuration

Example configuration for Claude Desktop or other MCP clients:

```json
{
  "odk_mcp_server": {
    "command": "python",
    "args": ["/path/to/pyodkmcp/odk_mcp_server.py"],
    "env": {
      "PYTHONPATH": "/path/to/pyodkmcp",
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

## 🛣️ Roadmap
- [ ] **Data Export**: Export synced tables to CSV/Excel.
- [ ] **Entity Support**: Integration with ODK Central Entities for longitudinal tracking.
- [ ] **Async DB**: Migration to `aiosqlite` for non-blocking I/O.
- [ ] **Version Monitoring**: Integration with `PyXComparer` to detect schema changes between syncs.

## 🤝 Community
If you find this server useful, please consider giving the repository a star!
