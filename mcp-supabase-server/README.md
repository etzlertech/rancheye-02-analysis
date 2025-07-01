# Supabase MCP Server

This MCP server enables Claude Desktop to interact directly with your Supabase database.

## Setup Instructions

### 1. Install Dependencies

```bash
cd mcp-supabase-server
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your Supabase credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual Supabase URL and anon key from your Supabase project settings.

### 3. Configure Claude Desktop

Add this server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "supabase": {
      "command": "node",
      "args": ["/Users/travisetzler/Documents/GitHub/rancheye-02-analysis/mcp-supabase-server/index.js"],
      "env": {
        "SUPABASE_URL": "your_supabase_url",
        "SUPABASE_ANON_KEY": "your_supabase_anon_key"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

Quit and restart Claude Desktop for the configuration to take effect.

## Available Tools

### query
Execute SELECT queries on your Supabase tables.

Example:
```
Use the query tool to select all rows from the analysis_configs table
```

### insert
Insert new data into tables.

Example:
```
Use the insert tool to add a new config to analysis_configs with name "test" and status "active"
```

### update
Update existing data in tables.

Example:
```
Use the update tool to set status to "completed" for task with id 123 in analysis_tasks
```

### delete
Delete data from tables.

Example:
```
Use the delete tool to remove configs with status "inactive" from analysis_configs
```

### rpc
Call Supabase RPC functions.

Example:
```
Use the rpc tool to call the get_analysis_stats function
```

## Troubleshooting

1. **Server not appearing in Claude Desktop**: Make sure the path in claude_desktop_config.json is absolute and correct.

2. **Authentication errors**: Verify your SUPABASE_URL and SUPABASE_ANON_KEY are correct.

3. **Permission errors**: Make sure your Supabase anon key has the necessary permissions for the operations you're trying to perform.

4. **Check logs**: Run the server manually to see error messages:
   ```bash
   node index.js
   ```