# Puppeteer MCP Quick Setup & Reference

## 🚀 Quick Setup (5 minutes)

### 1. Check Prerequisites
```bash
node --version  # Must have Node.js
```

### 2. Edit Claude Config
```bash
# Backup first
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/claude_config_backup.json

# Edit the file
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 3. Add Puppeteer to Config
```json
{
  "mcpServers": {
    "supabase": {
      // ... keep existing ...
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "PUPPETEER_LAUNCH_OPTIONS": "{ \"headless\": false, \"defaultViewport\": { \"width\": 1280, \"height\": 800 } }"
      }
    }
  }
}
```

### 4. Restart Claude Desktop
- Quit completely (Cmd+Q)
- Reopen Claude
- Look for MCP icon showing "puppeteer"

## 🎯 Common Commands

### Basic Navigation
```
Navigate to http://localhost:8080
Take screenshot "dashboard"
Refresh the page
Go back
```

### Interacting with Elements
```
Click button with text "Add Config"
Click element with id "saveBtn"
Fill input with id "configName" with "Gate Monitor"
Select "water_level" from dropdown with id "analysisType"
Hover over element with class "info-icon"
```

### Checking Elements
```
Check if element with id "errorMsg" exists
Get text content of element with class "status"
Count elements with class "analysis-card"
Check if element with id "loader" is visible
```

### Taking Screenshots
```
Take screenshot "analysis-dashboard"
Take screenshot "error-state-001"
Take screenshot "results/water-level-alert"
```

### JavaScript Execution
```
Execute JavaScript: document.querySelector('#results').children.length
Execute JavaScript: localStorage.getItem('authToken')
Evaluate: return document.title
```

## 🔧 RanchEye-02 Specific Examples

### Test Analysis Dashboard
```
Navigate to http://localhost:8080
Take screenshot "dashboard-initial"
Click "Add Analysis Config"
Fill #configName with "North Gate Monitor"
Select "gate_detection" from #analysisType
Click #saveConfig
Check if element with text "North Gate Monitor" exists
```

### Test Results Display
```
Navigate to http://localhost:8080/results
Count elements with class "result-card"
Click first element with class "view-details"
Take screenshot "result-details"
Check if element with class "ai-analysis" exists
```

### Test Alert System
```
Navigate to http://localhost:8080/alerts
Check if element with class "alert-critical" exists
Click first element with class "alert-item"
Take screenshot "alert-modal"
Click button with text "Acknowledge"
```

## 🛠️ Troubleshooting

### Browser Not Showing?
- Check `"headless": false` in config
- Restart Claude Desktop

### Can't Find Element?
```
// Debug with:
Execute JavaScript: document.querySelector('YOUR_SELECTOR')
Take screenshot "debug-current-state"
```

### MCP Not Connected?
1. Check JSON syntax in config
2. Run `npm list -g` to verify npm works
3. Restart Claude completely

## 💡 Pro Tips

1. **Always take screenshots** before and after actions
2. **Use specific selectors** (id > class > text)
3. **Add waits** for dynamic content:
   ```
   Wait 2 seconds
   Check if element exists (will retry)
   ```
4. **Chain actions** for complex flows
5. **Name screenshots** descriptively

## 📝 Example Development Session

```
You: "Create an analysis monitoring dashboard"
Claude: [Creates HTML/CSS/JS files]

You: "Show me the dashboard"
Claude: Navigate to http://localhost:8080
        Take screenshot "dashboard-v1"

You: "Add a real-time queue counter"
Claude: [Updates code]
        Refresh the page
        Take screenshot "dashboard-with-counter"

You: "Make it update every 5 seconds"
Claude: [Adds auto-refresh code]
        Wait 6 seconds
        Check if element #queueCount changed
        Take screenshot "dashboard-auto-updating"
```

## 🔗 Related Docs

- [Full Puppeteer MCP Guide](PUPPETEER_MCP_GUIDE.md) - Detailed setup and usage
- [MCP Integration Summary](MCP_INTEGRATION_SUMMARY.md) - All MCP tools overview
- [rancheye-01 UI Testing Guide](../rancheye-01/tests/ui/UI_TESTING_GUIDE.md) - Advanced testing patterns

Ready to build interactive UIs with real-time feedback! 🚀