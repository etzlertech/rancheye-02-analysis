# Supabase MCP Server Integration Guide

## Overview

This document explains how to leverage the Supabase MCP (Model Context Protocol) server that's already configured in your Claude desktop app for easy CRUD operations in the rancheye-02-analysis service.

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI assistants like Claude to interact directly with external services. In this case, it provides direct access to your Supabase database, enabling:

- Direct SQL query execution
- Table creation and management
- Data manipulation (INSERT, UPDATE, DELETE)
- Real-time data exploration
- Schema inspection

## Available MCP Commands

When working with Claude on this project, you have access to these Supabase operations:

### Database Operations

```sql
-- Create tables (executed via SQL editor)
CREATE TABLE IF NOT EXISTS table_name (...);

-- Query data
SELECT * FROM analysis_configs WHERE active = true;

-- Insert data
INSERT INTO analysis_tasks (image_id, config_id, priority) 
VALUES ('image123', 'config456', 5);

-- Update records
UPDATE analysis_tasks 
SET status = 'processing', started_at = NOW() 
WHERE id = 'task789';

-- Delete records
DELETE FROM analysis_cache WHERE expires_at < NOW();
```

### Table Operations

The following tables are used by rancheye-02-analysis:

1. **analysis_configs** - Analysis rule configurations
2. **analysis_tasks** - Task queue for pending analyses
3. **image_analysis_results** - Stores AI analysis results
4. **analysis_alerts** - Triggered alerts
5. **analysis_cache** - Cached results for cost optimization
6. **analysis_costs** - API usage tracking

## Using MCP with Claude

### 1. Direct Database Queries

Simply ask Claude to query or manipulate data:

```
"Show me all pending analysis tasks"
"Create a new gate detection config for the North Gate camera"
"Update the task status to completed for task ID xyz"
"Show me analysis results from the last 24 hours"
```

### 2. Schema Exploration

Ask Claude to explore the database structure:

```
"What columns are in the analysis_configs table?"
"Show me the relationships between the analysis tables"
"What indexes exist on the analysis_tasks table?"
```

### 3. Data Analysis

Claude can perform complex queries and analysis:

```
"Show me the average processing time by AI provider"
"Which cameras have the most alerts in the past week?"
"Calculate the total API costs for this month"
```

## Best Practices for AI-Assisted Development

### 1. Table Creation

When asking Claude to create tables, provide clear requirements:

```
"Create a table to store custom alert rules with fields for:
- Rule name
- Condition (JSON)
- Action to take
- Active status
- Priority level"
```

### 2. Data Validation

Ask Claude to validate data before operations:

```
"Before inserting this analysis config, check if a similar one already exists"
"Validate that all required fields are present in this task"
```

### 3. Performance Optimization

Leverage Claude's ability to optimize queries:

```
"Create an index to speed up queries for pending tasks"
"Optimize this query that finds unprocessed images"
```

## Example CRUD Operations for rancheye-02-analysis

### Create - Adding Analysis Configuration

```python
# Claude can help generate and execute this
config = {
    'name': 'Water Level Monitor - South Pasture',
    'camera_name': 'South Pasture Cam',
    'analysis_type': 'water_level',
    'model_provider': 'openai',
    'model_name': 'gpt-4-vision-preview',
    'prompt_template': '...detailed prompt...',
    'threshold': 0.8,
    'active': True
}

# Ask Claude: "Insert this water level monitoring config into analysis_configs"
```

### Read - Querying Analysis Results

```sql
-- Ask Claude: "Show me all low water level detections from this week"
SELECT 
    iar.*, 
    si.camera_name,
    ac.name as config_name
FROM image_analysis_results iar
JOIN spypoint_images si ON iar.image_id = si.image_id
JOIN analysis_configs ac ON iar.config_id = ac.id
WHERE iar.analysis_type = 'water_level'
    AND iar.result->>'water_level' IN ('LOW', 'EMPTY')
    AND iar.created_at > NOW() - INTERVAL '7 days'
ORDER BY iar.created_at DESC;
```

### Update - Modifying Task Status

```python
# Ask Claude: "Update all stuck processing tasks to pending status"
# Claude will help identify stuck tasks and update them safely
```

### Delete - Cleaning Up Old Cache

```sql
-- Ask Claude: "Clean up expired cache entries"
DELETE FROM analysis_cache 
WHERE expires_at < NOW() - INTERVAL '1 day';
```

## Integration with Python Code

When developing the service, you can ask Claude to generate Python code that integrates with the database:

```python
# Ask Claude: "Create a function to get the next pending task"
async def get_next_pending_task(supabase_client):
    """Fetch the highest priority pending task"""
    result = await supabase_client.table('analysis_tasks') \
        .select('*, analysis_configs(*)') \
        .eq('status', 'pending') \
        .order('priority', desc=True) \
        .limit(1) \
        .execute()
    
    return result.data[0] if result.data else None
```

## Monitoring and Debugging

Use Claude to help with monitoring queries:

```
"Show me the current task queue status"
"Find any failed tasks with their error messages"
"Calculate the success rate by analysis type"
"Show me tasks that have been retried multiple times"
```

## Advanced MCP Features

### 1. Transaction Management

While MCP doesn't directly support transactions, you can ask Claude to help design atomic operations:

```
"Create a process that atomically moves a task from pending to processing"
```

### 2. Real-time Monitoring

Ask Claude to create monitoring queries:

```
"Create a query to monitor the task queue depth in real-time"
"Show me the analysis throughput for the last hour"
```

### 3. Performance Analysis

```
"Analyze query performance for the most common operations"
"Suggest indexes to improve task fetching speed"
```

## Tips for Effective MCP Usage

1. **Be Specific**: Give Claude specific table names and column names
2. **Provide Context**: Explain the business logic behind your request
3. **Iterate**: Start simple and refine based on results
4. **Validate**: Ask Claude to verify data integrity after operations
5. **Document**: Request Claude to add comments explaining complex queries

## Common Patterns

### Queue Processing Pattern
```
"Create a query to fetch and lock the next task for processing"
"Update the task with results and unlock it"
"Handle task failures with retry logic"
```

### Alert Generation Pattern
```
"When analysis confidence is below threshold, create an alert"
"Check for duplicate alerts before creating new ones"
"Group related alerts together"
```

### Cost Tracking Pattern
```
"Update the daily cost summary after each analysis"
"Create a view showing costs by provider and model"
"Alert when daily costs exceed threshold"
```

## Security Considerations

- MCP uses the Service Role Key for full database access
- All operations are logged in Supabase
- Claude respects RLS policies if enabled
- Sensitive data should be handled carefully

## Getting Started

1. Ensure Claude desktop has the Supabase MCP server configured
2. Open this project in Claude
3. Start with simple queries to verify connection
4. Build up to complex CRUD operations
5. Use Claude to generate Python integration code

## Example Workflow

1. **Ask Claude**: "Show me the current analysis_configs"
2. **Review** the configurations
3. **Ask Claude**: "Create a new config for fence integrity monitoring"
4. **Verify**: "Show me the config we just created"
5. **Test**: "Create a test task for this new config"
6. **Monitor**: "Show me the task status"

With MCP integration, Claude becomes a powerful database assistant that can help you develop, debug, and optimize your rancheye-02-analysis service efficiently.