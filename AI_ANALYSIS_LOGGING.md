# AI Analysis Comprehensive Logging

This system now captures **ALL** AI analysis prompts and responses in a comprehensive PostgreSQL table for complete audit trail and cost tracking.

## What Gets Logged

Every AI analysis (both automated and user-initiated) saves the following data:

### Core Analysis Data
- **Image Information**: Image ID, URL, camera name, capture timestamp
- **Exact Prompt**: The complete prompt sent to the AI model
- **Model Details**: Provider (OpenAI/Gemini), model name, temperature, max tokens
- **Complete Response**: Raw AI response AND parsed JSON results
- **Performance**: Processing time, tokens used, estimated cost

### Context & Metadata
- **Analysis Type**: gate_detection, door_detection, water_level, etc.
- **Session Grouping**: Multi-model comparisons get the same session_id
- **User vs Automated**: Tracks whether analysis was user-initiated or automated
- **Custom Prompts**: Flags when custom prompts were used vs templates
- **Error Tracking**: Captures failures and error messages

## Database Table: `ai_analysis_logs`

### Key Fields
```sql
image_id TEXT               -- Links to the analyzed image
image_url TEXT              -- Direct URL to the image
prompt_text TEXT            -- Exact prompt sent to AI
raw_response TEXT           -- Complete AI response
parsed_response JSONB       -- Structured JSON result
model_provider TEXT         -- 'openai', 'gemini', 'anthropic'
model_name TEXT            -- 'gpt-4o-mini', 'gemini-1.5-flash', etc.
tokens_used INTEGER         -- For cost tracking
estimated_cost DECIMAL      -- Calculated cost in USD
session_id TEXT            -- Groups related analyses
user_initiated BOOLEAN     -- TRUE for test analyses
created_at TIMESTAMPTZ    -- When analysis was performed
```

## Cost Tracking Features

### Automatic Cost Calculation
- PostgreSQL function automatically calculates costs based on current model pricing
- Tracks per-model, per-day totals
- Supports different pricing for input/output tokens

### Cost Views
- `daily_ai_costs` - Daily cost breakdown by model
- `ai_model_performance` - Performance metrics and failure rates

## Usage Examples

### Get Recent Test Analyses
```python
logs = await supabase.get_recent_ai_analysis_logs(
    limit=50,
    user_initiated_only=True,
    analysis_type='door_detection'
)
```

### Cost Summary
```python
costs = await supabase.get_analysis_cost_summary(
    start_date='2024-01-01',
    end_date='2024-01-31'
)
```

### Find All Analyses for an Image
```sql
SELECT * FROM ai_analysis_logs 
WHERE image_id = 'your-image-id'
ORDER BY created_at;
```

### Model Comparison Session
```sql
SELECT model_provider, model_name, confidence, tokens_used, estimated_cost
FROM ai_analysis_logs 
WHERE session_id = 'session-uuid'
ORDER BY created_at;
```

## Integration Points

### Test Analysis Endpoint
- Every test analysis (single or multi-model) creates comprehensive logs
- Session IDs group related model comparisons
- Custom prompts are flagged appropriately

### Automated Analysis Service  
- All scheduled/automated analyses are logged
- Links to task IDs and config IDs for traceability
- Tracks primary, secondary, and tiebreaker model results

### Analysis Service
- Enhanced to save logs for every model execution
- Captures tiebreaker analyses with modified prompts
- Groups related analyses with session IDs

## Migration

1. **Create Table**: Run the SQL in `database/ai_analysis_logs.sql`
2. **Deploy Code**: The logging is automatic once table exists
3. **Verify**: Check logs after running test analyses

```bash
# Create the table (manual execution required)
psql -h your-supabase-host -U postgres -d postgres < database/ai_analysis_logs.sql

# Or use Supabase SQL editor to run the contents of ai_analysis_logs.sql
```

## Benefits

1. **Complete Audit Trail**: Every AI interaction is recorded
2. **Cost Monitoring**: Real-time cost tracking per model/analysis
3. **Performance Analysis**: Compare model accuracy and speed
4. **Debugging**: Full prompt/response data for troubleshooting
5. **Compliance**: Comprehensive logging for audit requirements
6. **Research**: Data for improving prompts and model selection

## Privacy & Storage

- Raw responses may contain analysis details about ranch operations
- Consider data retention policies for long-term storage
- Estimated storage: ~1-5KB per analysis depending on response length
- Automatic cost calculation reduces manual tracking overhead