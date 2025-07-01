# Puppeteer MCP Browser Automation Guide for RanchEye-02-Analysis

## Overview

This guide explains how to set up and use Puppeteer MCP (Model Context Protocol) for browser automation in the rancheye-02-analysis project. This is the same powerful browser control system used successfully in rancheye-01.

## What is Puppeteer MCP?

Puppeteer MCP allows Claude to:
- **Control a real Chrome browser** on your machine
- **Navigate to web pages** and interact with UI elements
- **Take screenshots** for visual validation
- **Execute JavaScript** in the browser context
- **Test user interfaces** interactively
- **Debug visual issues** in real-time

## How It Works

```
[Claude Desktop] <--MCP Protocol--> [Puppeteer Server] <--Controls--> [Chrome Browser]
       ↓                                                                      ↓
   Your Code                                                            Your Web App
```

When you ask Claude to interact with a browser, it uses MCP commands that control a local Puppeteer instance, which in turn controls Chrome on your machine.

## Installation & Setup

### Prerequisites

1. **Node.js** must be installed:
   ```bash
   # Check if installed
   node --version
   npm --version
   
   # Install if needed (macOS)
   brew install node
   ```

2. **Claude Desktop** must be running

### Configuration Steps

#### 1. Locate Claude's Configuration File

```bash
# macOS location
~/Library/Application Support/Claude/claude_desktop_config.json

# Create a backup first!
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.backup.json
```

#### 2. Edit Configuration

Add the Puppeteer MCP server to your configuration:

```json
{
  "mcpServers": {
    "supabase": {
      // ... your existing Supabase config ...
    },
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ],
      "env": {
        "PUPPETEER_LAUNCH_OPTIONS": "{ \"headless\": false, \"defaultViewport\": { \"width\": 1280, \"height\": 800 } }"
      }
    }
  }
}
```

**Important Settings:**
- `"headless": false` - Shows the browser window (recommended for development)
- `"defaultViewport"` - Sets initial browser size

#### 3. Restart Claude Desktop

1. Completely quit Claude Desktop (Cmd+Q on macOS)
2. Reopen Claude Desktop
3. Look for the MCP icon in Claude's interface
4. You should see both "supabase" and "puppeteer" listed

### Alternative: Playwright MCP

If Puppeteer has issues, you can use Playwright instead:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@executeautomation/playwright-mcp-server"
      ]
    }
  }
}
```

## Usage for RanchEye-02-Analysis

### 1. Building the Analysis Dashboard UI

When creating web interfaces for the analysis service:

```javascript
// Navigate to your development server
"Navigate to http://localhost:8080"

// Test the dashboard layout
"Take a screenshot of the analysis dashboard"

// Interact with analysis configurations
"Click the 'Add Analysis Config' button"
"Fill the input with id 'configName' with 'Gate Monitor - North'"
"Select 'gate_detection' from the analysis type dropdown"
"Click 'Save Configuration'"

// Verify the UI updated
"Check if element with text 'Gate Monitor - North' exists"
```

### 2. Testing Analysis Results Display

```javascript
// View analysis results
"Navigate to http://localhost:8080/results"
"Take screenshot of the results grid"

// Test filtering
"Select 'water_level' from the filter dropdown"
"Check how many result cards are visible"

// Test alert display
"Click on an alert notification"
"Verify the alert modal shows correct information"
```

### 3. Building Real-time Monitoring Dashboard

```javascript
// Test real-time updates
"Navigate to http://localhost:8080/monitor"
"Wait for 5 seconds"
"Check if the task queue count updated"
"Take screenshot of the monitoring dashboard"

// Test chart interactions
"Hover over the performance chart"
"Click on the 'Last 24 Hours' button"
"Verify the chart updated"
```

### 4. Configuration Management UI

```javascript
// Test config CRUD operations
"Navigate to http://localhost:8080/configs"
"Count the number of config cards"
"Click the edit button on the first config"
"Change the threshold value to 0.9"
"Click save"
"Verify the success message appears"
```

## Specific Test Scenarios for Analysis Service

### Testing Alert Visualization

```javascript
// Test alert timeline
"Navigate to http://localhost:8080/alerts"
"Take screenshot of alert timeline"
"Click on a critical alert"
"Verify the image preview loads"
"Check if the AI analysis details are displayed"
```

### Testing Cost Dashboard

```javascript
// Test cost tracking UI
"Navigate to http://localhost:8080/costs"
"Select date range for this month"
"Take screenshot of cost breakdown chart"
"Click on 'OpenAI' in the legend"
"Verify the chart updates to show only OpenAI costs"
```

### Testing Analysis Queue Management

```javascript
// Test queue visualization
"Navigate to http://localhost:8080/queue"
"Check the pending tasks count"
"Click 'Process Next' button"
"Wait for status to change to 'processing'"
"Verify the UI updates in real-time"
```

## Integration with Development Workflow

### 1. Rapid UI Prototyping

```
You: "Create a dashboard showing analysis performance metrics"
Claude: [Creates HTML/CSS/JS files]
You: "Show me how it looks"
Claude: [Navigates to page, takes screenshot]
You: "The charts are too small"
Claude: [Adjusts CSS, refreshes, shows updated view]
```

### 2. Visual Regression Testing

```javascript
// Capture baseline
"Navigate to http://localhost:8080"
"Take screenshot 'dashboard-baseline'"

// After making changes
"Navigate to http://localhost:8080"
"Take screenshot 'dashboard-updated'"
// Claude can compare and highlight differences
```

### 3. Debugging UI Issues

```javascript
// Inspect element states
"Execute JavaScript: document.querySelector('.error-message').innerText"
"Check if element with class 'loading-spinner' is visible"
"Get the computed style of element with id 'chartContainer'"
```

## Best Practices

### 1. Development Setup

- Run your web server before testing
- Use consistent viewport sizes
- Clear browser cache between major tests
- Keep the browser window visible for debugging

### 2. Screenshot Management

```javascript
// Organized screenshot naming
"Take screenshot 'analysis/configs/add-config-form'"
"Take screenshot 'analysis/results/water-level-low'"
"Take screenshot 'analysis/alerts/critical-gate-open'"
```

### 3. Error Handling

```javascript
// Check for errors before proceeding
"Check if element with class 'error-message' exists"
"If error exists, get its text content"
"Take screenshot 'error-state'"
```

## Common Commands Reference

### Navigation & Screenshots
- `Navigate to [URL]`
- `Take screenshot "[name]"`
- `Go back`
- `Refresh the page`

### Element Interaction
- `Click [selector or text]`
- `Fill [selector] with "[value]"`
- `Select "[option]" from [selector]`
- `Hover over [selector]`

### Validation
- `Check if element [selector] exists`
- `Get text content of [selector]`
- `Count elements with [selector]`
- `Check if [selector] is visible`

### JavaScript Execution
- `Execute JavaScript: [code]`
- `Evaluate: return [expression]`

## Troubleshooting

### MCP Not Connecting

1. Verify JSON syntax in config file
2. Ensure Node.js is installed and in PATH
3. Check Claude Desktop logs: `~/Library/Logs/Claude/`
4. Try restarting your computer

### Browser Control Issues

1. Browser window not appearing: Check `headless` is set to `false`
2. Elements not found: Verify selectors are correct
3. Timeouts: Increase wait times for slow-loading pages
4. Chrome not installed: Install Chrome or use Playwright

### Permission Issues

- macOS may require accessibility permissions
- Check System Preferences > Security & Privacy
- Grant permissions to Claude Desktop if prompted

## Example Workflow for Analysis Dashboard

```javascript
// 1. Start your development server
"Open terminal and run: cd rancheye-02-analysis && python -m src.web_server"

// 2. Navigate to dashboard
"Navigate to http://localhost:8080"

// 3. Test the layout
"Take screenshot 'initial-dashboard'"
"Check if element with id 'analysisQueue' exists"
"Check if element with id 'performanceChart' exists"

// 4. Test interactions
"Click button with text 'Add Analysis Rule'"
"Fill input with id 'ruleName' with 'Test Rule'"
"Select 'gate_detection' from dropdown with id 'analysisType'"
"Click button with text 'Save'"

// 5. Verify results
"Check if element with text 'Test Rule' exists"
"Take screenshot 'after-adding-rule'"
```

## Benefits for RanchEye-02-Analysis

1. **Rapid Dashboard Development**: See changes instantly
2. **Visual Validation**: Ensure UI matches design
3. **Interactive Testing**: Test complex workflows
4. **Real-time Debugging**: Fix issues immediately
5. **Documentation**: Auto-generate UI screenshots

## Next Steps

1. Set up Puppeteer MCP following the configuration steps
2. Restart Claude Desktop
3. Start building your analysis dashboard
4. Use browser automation to test and refine
5. Create visual regression tests for stability

With Puppeteer MCP, you can rapidly develop and test the web interface for your analysis service, ensuring a polished user experience for monitoring ranch conditions!