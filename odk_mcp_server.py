"""
ODK MCP Server module for listing projects, forms, and fetching submission data.
"""

import asyncio, pandas as pd
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from pyodk.client import Client
import sqlite3, datetime

# Initialize MCP server
mcp = FastMCP(name="odk-mcp")
conn= sqlite3.connect("D://odk_mcp_server.db")

# Initialize ODK Client
client = Client()

@mcp.tool()
async def list_projects() -> list:
    """List all projects for the user."""
    return [{"project_id": str(p.id), "name": p.name} for p in client.projects.list()]
    # return [{"id":0,"name":"Test Project Name"}]

@mcp.tool()
async def list_forms(project_id: int ) -> list:
    """List forms in a project."""
    return client.forms.list(project_id=str(project_id))
    # return [{"id":0,"name":"Test Project Form0"},{"id":1,"name":"Test Project Form1"}]

@mcp.tool()
async def get_data(project_id_str: str, form_id_str: str) -> list:
    """Fetch form submission data."""
    data=client.submissions.get_table(project_id=project_id_str, form_id=form_id_str)
    data=data['value']
    if not data:
        return {}
    else:
        df= pd.json_normalize(data)
        tbl_name= 'data_pid_'+project_id_str+'__fid_'+form_id_str.replace(' ','_').replace('-','_')
        df.to_sql(tbl_name, conn, if_exists='replace', index=False)
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        t_data = {'table': [tbl_name], 'update_ts': [str(now)]}
        time_df = pd.DataFrame(t_data)
        time_df.to_sql('table_log', conn, if_exists='append', index=False)
        
        return df.head(50).to_dict(orient='records')
    # return [{"id":0,"name":"Test Submission 0"},{"id":1,"name":"Test Submission 1"}]

if __name__ == "__main__":
    asyncio.run(mcp.run())
