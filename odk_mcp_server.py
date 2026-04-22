"""
ODK MCP Server module for listing projects, forms, and fetching submission data.
"""

import asyncio
import pandas as pd
import sqlite3
import datetime
import logging
import os
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from pyodk.client import Client

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("odk-mcp")

# Initialize MCP server
mcp = FastMCP(name="odk-mcp")

# Database Configuration: Use environment variable or default to local path
DB_PATH = os.getenv("ODK_MCP_DB_PATH", "odk_mcp_server.db")
logger.info(f"Initializing ODK MCP Server. Database path: {DB_PATH}")

def get_db_connection():
    """Returns a sqlite3 connection to the configured database."""
    return sqlite3.connect(DB_PATH)

# Initialize ODK Client
try:
    client = Client()
    logger.info("PyODK Client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize PyODK Client: {e}")
    client = None

@mcp.tool()
async def list_projects() -> list:
    """List all projects for the user."""
    if not client:
        return [{"error": "ODK Client not initialized. Check your PyODK configuration."}]

    try:
        logger.info("Fetching project list from ODK Central...")
        projects = client.projects.list()
        result = [{"project_id": str(p.id), "name": p.name} for p in projects]
        logger.info(f"Successfully retrieved {len(result)} projects.")
        return result
    except Exception as e:
        logger.exception(f"Error listing projects: {e}")
        return [{"error": f"Failed to list projects: {str(e)}"}]

@mcp.tool()
async def list_forms(project_id: int) -> list:
    """List forms in a project."""
    if not client:
        return [{"error": "ODK Client not initialized."}]

    try:
        logger.info(f"Fetching forms for project_id: {project_id}...")
        forms = client.forms.list(project_id=str(project_id))
        logger.info(f"Successfully retrieved {len(forms)} forms.")
        return forms
    except Exception as e:
        logger.exception(f"Error listing forms for project {project_id}: {e}")
        return [{"error": f"Failed to list forms: {str(e)}"}]

@mcp.tool()
async def get_data(project_id_str: str, form_id_str: str) -> list:
    """Fetch form submission data and store it in the local SQLite database."""
    if not client:
        return [{"error": "ODK Client not initialized."}]

    try:
        logger.info(f"Fetching data for project {project_id_str}, form {form_id_str}...")
        response = client.submissions.get_table(project_id=project_id_str, form_id=form_id_str)
        data = response.get('value', [])

        if not data:
            logger.warning(f"No data found for project {project_id_str}, form {form_id_str}.")
            return [{"message": "No submissions found for this form."}]

        # Process data
        df = pd.json_normalize(data)
        tbl_name = f"data_pid_{project_id_str}__fid_{form_id_str.replace(' ', '_').replace('-', '_')}"

        # Database operations
        with get_db_connection() as conn:
            # Store submission data
            df.to_sql(tbl_name, conn, if_exists='replace', index=False)

            # Update table log
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            t_data = {'table': [tbl_name], 'update_ts': [str(now)]}
            time_df = pd.DataFrame(t_data)
            time_df.to_sql('table_log', conn, if_exists='append', index=False)

        logger.info(f"Successfully synced {len(df)} records to table {tbl_name}.")
        return df.head(50).to_dict(orient='records')

    except Exception as e:
        logger.exception(f"Critical error during get_data for project {project_id_str}, form {form_id_str}: {e}")
        return [{"error": f"Failed to fetch and store data: {str(e)}"}]

if __name__ == "__main__":
    asyncio.run(mcp.run())
