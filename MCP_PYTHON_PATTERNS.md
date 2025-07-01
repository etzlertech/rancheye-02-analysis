# MCP Python Integration Patterns

## Overview

This guide shows how to leverage Claude's MCP database access to generate Python code for the rancheye-02-analysis service. Use these patterns to quickly build database operations.

## 🔧 Core Database Client Setup

Ask Claude to help set up your database client:

```python
# "Create a Supabase database client with connection pooling"
from supabase import create_client, Client
from typing import Optional
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get or create Supabase client (singleton)"""
    return create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_KEY']
    )
```

## 📝 Common Database Operations

### 1. Task Queue Management

Ask Claude: **"Create a TaskManager class for handling the analysis queue"**

```python
class TaskManager:
    def __init__(self):
        self.client = get_supabase_client()
    
    async def get_next_task(self) -> Optional[dict]:
        """Fetch highest priority pending task"""
        result = self.client.table('analysis_tasks') \
            .select('*, analysis_configs(*)') \
            .eq('status', 'pending') \
            .order('priority', desc=True) \
            .limit(1) \
            .execute()
        
        if result.data:
            task = result.data[0]
            # Mark as processing
            self.client.table('analysis_tasks') \
                .update({'status': 'processing', 'started_at': 'now()'}) \
                .eq('id', task['id']) \
                .execute()
            return task
        return None
    
    async def complete_task(self, task_id: str, success: bool, error: str = None):
        """Mark task as completed or failed"""
        update_data = {
            'status': 'completed' if success else 'failed',
            'completed_at': 'now()'
        }
        if error:
            update_data['error_message'] = error
            
        self.client.table('analysis_tasks') \
            .update(update_data) \
            .eq('id', task_id) \
            .execute()
```

### 2. Analysis Results Storage

Ask Claude: **"Create a function to save analysis results with caching"**

```python
async def save_analysis_result(
    image_id: str,
    config_id: str,
    result: dict,
    processing_time_ms: int,
    tokens_used: int = None
) -> str:
    """Save analysis result and check for alerts"""
    client = get_supabase_client()
    
    # Check cache first
    cache_key = f"{image_id}:{config_id}"
    
    # Save result
    analysis_result = {
        'image_id': image_id,
        'config_id': config_id,
        'result': result,
        'confidence': result.get('confidence', 0),
        'processing_time_ms': processing_time_ms,
        'tokens_used': tokens_used,
        'alert_triggered': result.get('confidence', 0) > 0.8
    }
    
    response = client.table('image_analysis_results') \
        .insert(analysis_result) \
        .execute()
    
    return response.data[0]['id']
```

### 3. Configuration Management

Ask Claude: **"Create a config loader with caching"**

```python
class ConfigManager:
    def __init__(self):
        self.client = get_supabase_client()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def get_active_configs(self, camera_name: str = None) -> list:
        """Get active analysis configurations"""
        cache_key = f"configs:{camera_name or 'all'}"
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Query database
        query = self.client.table('analysis_configs') \
            .select('*') \
            .eq('active', True)
        
        if camera_name:
            query = query.or_(f'camera_name.eq.{camera_name},camera_name.is.null')
        
        result = query.execute()
        
        # Cache result
        self._cache[cache_key] = result.data
        return result.data
```

### 4. Alert Generation

Ask Claude: **"Create an alert system that prevents duplicates"**

```python
class AlertManager:
    def __init__(self):
        self.client = get_supabase_client()
    
    async def create_alert(
        self,
        analysis_result_id: str,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        camera_name: str,
        alert_data: dict = None
    ):
        """Create alert if not duplicate"""
        # Check for recent similar alerts
        recent_check = self.client.table('analysis_alerts') \
            .select('id') \
            .eq('camera_name', camera_name) \
            .eq('alert_type', alert_type) \
            .gte('created_at', 'now() - interval \'1 hour\'') \
            .execute()
        
        if recent_check.data:
            print(f"Similar alert exists, skipping: {title}")
            return None
        
        # Create new alert
        alert = {
            'analysis_result_id': analysis_result_id,
            'alert_type': alert_type,
            'severity': severity,
            'title': title,
            'message': message,
            'camera_name': camera_name,
            'alert_data': alert_data or {}
        }
        
        result = self.client.table('analysis_alerts') \
            .insert(alert) \
            .execute()
        
        return result.data[0]['id']
```

## 🔄 Batch Operations

Ask Claude: **"Create batch processing for multiple images"**

```python
async def create_batch_tasks(image_ids: list[str], config_id: str):
    """Create analysis tasks for multiple images"""
    client = get_supabase_client()
    
    # Build batch insert data
    tasks = [
        {
            'image_id': image_id,
            'config_id': config_id,
            'priority': 5,
            'status': 'pending'
        }
        for image_id in image_ids
    ]
    
    # Insert with upsert to handle duplicates
    result = client.table('analysis_tasks') \
        .upsert(tasks, on_conflict='image_id,config_id') \
        .execute()
    
    return len(result.data)
```

## 📊 Monitoring Queries

Ask Claude: **"Create monitoring functions for the dashboard"**

```python
class MonitoringService:
    def __init__(self):
        self.client = get_supabase_client()
    
    def get_queue_status(self) -> dict:
        """Get current queue statistics"""
        result = self.client.rpc('get_queue_status').execute()
        return result.data
    
    def get_performance_metrics(self, hours: int = 24) -> dict:
        """Get performance metrics for the last N hours"""
        query = f"""
        SELECT 
            model_provider,
            COUNT(*) as total,
            AVG(processing_time_ms) as avg_time,
            AVG(confidence) as avg_confidence
        FROM image_analysis_results
        WHERE created_at > NOW() - INTERVAL '{hours} hours'
        GROUP BY model_provider
        """
        
        # Note: For complex queries, ask Claude to help create database functions
        return self.client.rpc('get_performance_metrics', {'hours': hours}).execute().data
```

## 🛡️ Error Handling

Ask Claude: **"Add robust error handling to database operations"**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class DatabaseService:
    def __init__(self):
        self.client = get_supabase_client()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def safe_insert(self, table: str, data: dict) -> dict:
        """Insert with retry logic"""
        try:
            result = self.client.table(table).insert(data).execute()
            return result.data[0]
        except Exception as e:
            print(f"Database error: {e}")
            raise
    
    async def transaction_example(self, task_id: str, result_data: dict):
        """Example of pseudo-transaction pattern"""
        try:
            # Start by updating task
            self.client.table('analysis_tasks') \
                .update({'status': 'processing'}) \
                .eq('id', task_id) \
                .execute()
            
            # Save result
            result = await self.safe_insert('image_analysis_results', result_data)
            
            # Complete task
            self.client.table('analysis_tasks') \
                .update({'status': 'completed'}) \
                .eq('id', task_id) \
                .execute()
            
            return result
            
        except Exception as e:
            # Rollback task status
            self.client.table('analysis_tasks') \
                .update({'status': 'failed', 'error_message': str(e)}) \
                .eq('id', task_id) \
                .execute()
            raise
```

## 🚀 Quick MCP Commands

When developing, use these commands with Claude:

1. **"Generate the database access layer for analysis_configs"**
2. **"Create a cache-aware query for expensive operations"**
3. **"Build a retry mechanism for failed tasks"**
4. **"Design a cost tracking system for API usage"**
5. **"Create helper functions for common queries"**

## 💡 Best Practices

1. **Use MCP for Prototyping**: Ask Claude to test queries before implementing
2. **Generate Type Hints**: Request fully typed Python code
3. **Request Tests**: Ask for unit tests with mocked database calls
4. **Performance First**: Ask Claude to optimize queries for your use case
5. **Error Scenarios**: Request error handling for edge cases

## Example Development Flow

1. **Start with MCP**: "Show me the analysis_tasks schema"
2. **Test Query**: "Find tasks that have been stuck in processing for over an hour"
3. **Generate Code**: "Create a Python function to reset stuck tasks"
4. **Add Tests**: "Write unit tests for the task reset function"
5. **Optimize**: "How can I make this query more efficient?"

Remember: Claude can see your database schema and data through MCP, so leverage this for rapid development!