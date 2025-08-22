### 🚀 ODK Central MCP Server

A Model Context Protocol (MCP) Server for ODK Central, enabling AI agents to interact with your data collection projects and forms. This server works in tandem with a separate dedicated **Python Database MCP Server** to provide a seamless and powerful ODK data analysis experience on AI Chatbot Applications like Claude Desktop & VS Code. Leverage the power of this server to bring your ODK workflow into the age of AI-powered assistants.

***

### 🛠️ Tools and Dual-Server Workflow

This setup utilizes two separate, but interconnected, MCP servers to create a robust agentic workflow. This design allows for both direct interaction with ODK Central and sophisticated querying of locally stored data. 

#### 1. `list_projects()`
This tool fetches and returns a list of all projects on the ODK Central server. It's the first step for an AI agent to understand your data collection projects.

#### 2. `list_forms(project_id: int)`
This tool retrieves a list of all forms within a specific ODK Central project, allowing the agent to navigate your data structure.

#### 3. `get_data(project_id_str: str, form_id_str: str)`
This is the central data retrieval tool. It fetches submission data for a specified form and performs a critical two-part action:
- It saves the fetched data into a local database table. The table is automatically named using a combination of the **project ID and form ID** for easy identification.
- It provides the user with a summary of the data from a small sample, giving a quick overview without overwhelming them.

***

### 🤝 The Integrated Database MCP Workflow

The true power of this setup lies in the **synergy between the two servers**. After the `get_data` tool has been used, the AI agent can transition to using the (Python Database MCP Server)[https://github.com/joybindroo/pyMCP] for follow-up queries. You can read more about installing and using this on the Github Repository page (https://github.com/joybindroo/pyMCP)[https://github.com/joybindroo/pyMCP]

Once both the ODK MCP Server and the Database MCP Server are setup and running in VS Code or Claude Desktop, the user can use natural language to know details about projects and forms of interest, download latest data of the required form and do data analysis from the local database.

For example, a user could type:

> "How many projects are there"
or
> "Which projects are running in Bihar and Jharkhand "

The AI will execute this action and provide a list of the projects accessible to the ODK Central user setup in the PyODK's config. From that point on, in the same chat session, the user can ask for details about the forms existing in the projects.

> "get forms in project abc"
The AI will execute this action and provide a list of forms existing in abc project.

The user can then ask the AI:
> "get data of form xyz"
or
> "get data of all the forms in project A and project B"
or
> "get data of daily reportin form from ABC project"

The AI will execute this action, store the data locally, and provide a brief summary. From that point on, in the same chat session, the user can ask detailed analytical questions without needing to perform another `get_data` call.

The user can then ask the AI:
> "search my ODK MCP server and look for the `xyz` table in the database and provide me with the count of submissions"


The AI recognizes this is a database query and seamlessly switches to using the **Database MCP Server**. It translates the natural language request into a precise SQL query, runs it against the local database, and provides the result. This allows for complex analytical queries to be resolved quickly and efficiently, turning your chat with the AI into a powerful data analysis tool.


# PyODK MCP Server Setup & Configuration

## Installation

1. **Clone or download this repository**

2. **Create and activate a virtual environment (recommended):**
Install Python version 3.12 or higher then create a virtual environment
```bash
# Create Virtual env.
py --3.12 -m venv venv

# Activate Virtual env.
# On Windows
venv\Scripts\activate
# On Linux/Unix or MacOS
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Save the server script** as `odk_mcp_server.py`

3. **Make it executable:**
```bash
chmod +x odk_mcp_server.py
```

## MCP Client Configuration

### For Claude Desktop App & Other MCP Clients


```json
{
   "odk_mcp_server": {
    "command": "your_path//pyodkmcp//venv//Scripts//python.exe",
    "args": [
      "your_path//pyodkmcp//odk_mcp_server.py"
      ],
    "env": {
      "PYTHONPATH": "path//pyodkmcp"
      }
  },
    "odk_mcp_sqlite_data": {
      "command": "your_path//pymcp//venv//Scripts//python.exe",
      "args": [
        "your_path//pymcp//db_mcp_server.py",
        "sqlite://your_path//odk_mcp_server.db"
      ],
      "env": {
        "PYTHONPATH": "your_path//mypymcp"
      }
    }
}
```

## Environment Configuration

By default the server will run using (PyODK's configuration)[https://github.com/getodk/pyodk?tab=readme-ov-file#configure]



## Troubleshooting

### Common Issues

1. **Connection Failed:**
   - Verify ODK Central URL is correct
   - Check username/password
   - Ensure ODK Central server is accessible

2. **Permission Denied:**
   - Verify user has appropriate permissions in ODK Central
   - Check project access rights


``
