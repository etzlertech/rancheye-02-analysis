-- Add input_tokens and output_tokens columns to ai_analysis_logs table
-- These are needed for accurate cost calculation

ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS input_tokens INTEGER,
ADD COLUMN IF NOT EXISTS output_tokens INTEGER;

-- Update the daily_ai_costs view to include token breakdown
DROP VIEW IF EXISTS daily_ai_costs;
CREATE VIEW daily_ai_costs AS
SELECT 
    created_at::date as analysis_date,
    model_provider,
    model_name,
    COUNT(*) as analysis_count,
    SUM(tokens_used) as total_tokens,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(estimated_cost) as total_cost,
    AVG(confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE analysis_successful = FALSE) as failed_count
FROM ai_analysis_logs
GROUP BY created_at::date, model_provider, model_name
ORDER BY analysis_date DESC, total_cost DESC;

-- Add index for cost queries with token fields
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_tokens ON ai_analysis_logs(input_tokens, output_tokens) 
WHERE input_tokens IS NOT NULL AND output_tokens IS NOT NULL;