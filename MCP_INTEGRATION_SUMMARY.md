# MCP Integration Summary for RanchEye-02-Analysis

> **⚠️ IMPORTANT**: MCP servers are ONLY available in Claude Desktop app, NOT in Claude Code (VS Code/Cursor extensions). See [`CLAUDE_DESKTOP_VS_CODE.md`](CLAUDE_DESKTOP_VS_CODE.md) for workflow strategies.

## What's Configured

Your rancheye-02-analysis project can leverage two powerful MCP servers:

1. **Supabase MCP** - Database access (already configured in rancheye-01)
2. **Puppeteer MCP** - Browser automation for UI development

## Supabase MCP

Provides seamless database access through Claude for all analysis tables.

### Key Benefits

1. **Direct Database Access**: Claude can read/write to all analysis tables
2. **Rapid Development**: Generate database code instantly
3. **Live Testing**: Test queries before implementing
4. **Data Exploration**: Understand your data structure in real-time
5. **Debugging**: Troubleshoot data issues interactively

## Available Tables

### Read Access (from rancheye-01)
- `spypoint_images` - Source images for analysis

### Full CRUD Access (rancheye-02-analysis)
- `analysis_configs` - AI analysis configurations
- `analysis_tasks` - Processing queue
- `image_analysis_results` - Analysis outputs
- `analysis_alerts` - Generated alerts
- `analysis_cache` - Result caching
- `analysis_costs` - Usage tracking

## Quick Start Examples

### 1. Create Your First Analysis Config
```
"Create a gate detection config for the Main Gate camera using GPT-4 Vision"
```

### 2. Check Task Queue
```
"Show me the current task queue status"
```

### 3. Generate Python Code
```
"Create a Python function to fetch and process the next pending task"
```

### 4. Monitor Performance
```
"Show me analysis performance metrics for the last 24 hours"
```

## Puppeteer MCP

Enables browser automation for building and testing web interfaces.

### Key Benefits

1. **Visual Development**: See UI changes in real-time
2. **Interactive Testing**: Click, type, and navigate
3. **Screenshot Capture**: Document UI states
4. **JavaScript Execution**: Debug in browser context
5. **Rapid Iteration**: Fix issues immediately

### Quick Setup

1. Add to Claude config (see [`PUPPETEER_MCP_GUIDE.md`](PUPPETEER_MCP_GUIDE.md))
2. Restart Claude Desktop
3. Start using browser commands

### Example Commands

```
Navigate to http://localhost:8080
Take screenshot "analysis-dashboard"
Click button with text "Add Config"
Fill input with id "configName" with "Gate Monitor"
```

## Documentation Structure

### Database MCP Docs

1. **[MCP_DATABASE_GUIDE.md](MCP_DATABASE_GUIDE.md)**
   - Comprehensive MCP overview
   - Available commands
   - Best practices
   - Advanced features

2. **[MCP_QUICK_REFERENCE.md](MCP_QUICK_REFERENCE.md)**
   - Quick CRUD examples
   - Common queries
   - Cheat sheet format

3. **[MCP_PYTHON_PATTERNS.md](MCP_PYTHON_PATTERNS.md)**
   - Python code generation
   - Database client patterns
   - Error handling
   - Performance optimization

### Browser MCP Docs

4. **[PUPPETEER_MCP_GUIDE.md](PUPPETEER_MCP_GUIDE.md)**
   - Complete setup instructions
   - Browser automation concepts
   - UI development workflow
   - Troubleshooting

5. **[PUPPETEER_QUICK_START.md](PUPPETEER_QUICK_START.md)**
   - 5-minute setup
   - Common commands reference
   - Quick examples
   - Pro tips

## Development Workflow

1. **Explore**: Ask Claude to show current data
2. **Design**: Test queries interactively
3. **Generate**: Request Python implementation
4. **Test**: Verify with real data
5. **Refine**: Optimize based on results

## Tips for Success

- **Be Specific**: Include table and column names
- **Test First**: Try queries in MCP before coding
- **Iterate**: Start simple, add complexity
- **Monitor**: Check performance regularly
- **Document**: Ask Claude to comment code

## Example Session

```
You: "Show me all active analysis configs"
Claude: [displays current configs]

You: "Create a water level monitor for South Pasture"
Claude: [creates config, shows result]

You: "Generate Python code to process water level analyses"
Claude: [provides complete implementation]

You: "Test it with image ID abc123"
Claude: [runs analysis, shows results]
```

## Combined Workflow Example

Using both MCP tools together for full-stack development:

```
# 1. Create analysis config via database
You: "Create a water level monitoring config"
Claude: [Creates config in database]

# 2. Build UI to display it
You: "Create a web dashboard showing all configs"
Claude: [Creates HTML/CSS/JS files]

# 3. Test the UI
You: "Show me the dashboard"
Claude: Navigate to http://localhost:8080
        Take screenshot "configs-dashboard"

# 4. Verify data appears
You: "Check if the water level config is displayed"
Claude: Check if element with text "Water Level Monitor" exists
        [Confirms it's visible]

# 5. Test interactions
You: "Click edit on the water level config"
Claude: Click button with class "edit-btn" in element containing "Water Level Monitor"
        Take screenshot "edit-form"

# 6. Update via UI and verify in DB
You: "Change threshold to 0.75 and save"
Claude: Fill input with id "threshold" with "0.75"
        Click button with text "Save"
        [Then queries database to confirm update]
```

This seamless integration accelerates development by providing immediate feedback at every layer of your application!

## Connection Details

- **Supabase Project**: enoyydytzcgejwmivshz
- **Shared with**: rancheye-01
- **Access Level**: Full CRUD on analysis tables
- **Authentication**: Service Role Key

The MCP integration is ready to accelerate your development!