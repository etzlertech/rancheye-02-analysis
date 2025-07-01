# Quick MCP CRUD Reference for RanchEye-02-Analysis

## 🚀 Quick Start

When using Claude with this project, you have direct database access via MCP. Just ask naturally!

## 📊 Common Database Operations

### View Data
```
"Show me all analysis configs"
"List pending tasks"
"Show today's analysis results"
"What alerts were triggered this week?"
```

### Create Records
```
"Add a gate detection config for North Gate camera"
"Create a water level monitoring rule"
"Insert a test task for image ID abc123"
```

### Update Records
```
"Mark task 123 as completed"
"Disable the water monitor config"
"Update the alert threshold to 0.9"
"Set all failed tasks back to pending"
```

### Delete Records
```
"Remove expired cache entries"
"Delete the test configuration"
"Clean up completed tasks older than 30 days"
```

## 🎯 Specific Examples for Each Table

### analysis_configs
```
"Create a config to detect open gates using GPT-4 Vision"
"Show all active water level monitors"
"Update the prompt template for animal detection"
"Disable all configs for maintenance"
```

### analysis_tasks
```
"Show the task queue status"
"Create tasks for all images from today"
"Reset failed tasks for retry"
"What's the oldest pending task?"
```

### image_analysis_results
```
"Show all gate detections where gate was open"
"Find low confidence results that need review"
"Calculate average processing time by model"
"Export today's results as CSV"
```

### analysis_alerts
```
"Show unacknowledged critical alerts"
"Create an alert for low water detection"
"Mark alerts as acknowledged"
"Find alerts for North Pasture camera"
```

## 💡 Pro Tips

1. **Use Natural Language**: "Find all images analyzed yesterday that detected animals"

2. **Complex Queries**: "Show me cameras with the most alerts, grouped by alert type"

3. **Data Validation**: "Before creating this config, check if it already exists"

4. **Performance**: "What queries are running slowly? Suggest indexes"

5. **Monitoring**: "Create a dashboard query showing system health"

## 🔧 Development Helpers

```
"Generate Python code to fetch the next task"
"Create a function to save analysis results"
"Write a query to calculate today's API costs"
"Build a method to check for duplicate alerts"
```

## 📈 Analysis Queries

```
"What's our AI API usage by provider?"
"Which analysis types have the highest accuracy?"
"Show cost trends for the past week"
"Find images that haven't been analyzed yet"
```

## ⚡ Quick Patterns

### Process Next Task
```
1. "Get the highest priority pending task"
2. "Update it to processing status"
3. "Save the analysis results"
4. "Mark task as completed"
```

### Handle Failures
```
1. "Find tasks that failed"
2. "Check their retry count"
3. "Reset tasks with retries remaining"
4. "Log permanent failures"
```

### Generate Reports
```
"Daily summary of analyses performed"
"Alert summary by camera location"
"Cost breakdown by AI provider"
"Performance metrics for the week"
```

Remember: Claude has full access to your Supabase database through MCP. Just describe what you want to do, and Claude will help execute it!