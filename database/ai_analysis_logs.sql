-- AI Analysis Comprehensive Logging Table
-- This table stores EVERY AI analysis request/response for complete audit trail

CREATE TABLE IF NOT EXISTS ai_analysis_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Image Information
    image_id TEXT NOT NULL,
    image_url TEXT,
    camera_name TEXT,
    captured_at TIMESTAMPTZ,
    
    -- Analysis Request Details
    analysis_type TEXT NOT NULL,
    prompt_text TEXT NOT NULL, -- The exact prompt sent to the AI
    custom_prompt BOOLEAN DEFAULT FALSE, -- Whether this was a custom prompt vs template
    
    -- AI Model Information
    model_provider TEXT NOT NULL, -- 'openai', 'gemini', 'anthropic'
    model_name TEXT NOT NULL, -- 'gpt-4o-mini', 'gemini-1.5-flash', etc.
    model_temperature FLOAT DEFAULT 0.3,
    max_tokens INTEGER DEFAULT 500,
    
    -- AI Response
    raw_response TEXT NOT NULL, -- Complete raw response from AI
    parsed_response JSONB, -- Parsed JSON response (if successful)
    
    -- Analysis Results
    confidence FLOAT,
    analysis_successful BOOLEAN DEFAULT TRUE,
    error_message TEXT, -- If analysis failed
    
    -- Performance Metrics
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    estimated_cost DECIMAL(10, 6), -- Cost in USD
    
    -- Context Information
    config_id UUID, -- Reference to analysis_configs if from automated analysis
    task_id UUID, -- Reference to analysis_tasks if from task queue
    session_id TEXT, -- For grouping related analyses (e.g., multi-model comparison)
    user_initiated BOOLEAN DEFAULT FALSE, -- TRUE for test analyses, FALSE for automated
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET, -- For user-initiated analyses
    user_agent TEXT, -- For user-initiated analyses
    
    -- Additional context
    notes TEXT, -- Any additional notes or context
    tags TEXT[], -- For categorization/filtering
    
    CONSTRAINT fk_ai_analysis_config FOREIGN KEY (config_id) REFERENCES analysis_configs(id) ON DELETE SET NULL,
    CONSTRAINT fk_ai_analysis_task FOREIGN KEY (task_id) REFERENCES analysis_tasks(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_image_id ON ai_analysis_logs(image_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_created_at ON ai_analysis_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_model ON ai_analysis_logs(model_provider, model_name);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_analysis_type ON ai_analysis_logs(analysis_type);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_session_id ON ai_analysis_logs(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_user_initiated ON ai_analysis_logs(user_initiated, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_config_id ON ai_analysis_logs(config_id) WHERE config_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_error ON ai_analysis_logs(analysis_successful, error_message) WHERE NOT analysis_successful;

-- Partial index for successful analyses with high confidence
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_high_confidence ON ai_analysis_logs(confidence, created_at DESC) 
WHERE analysis_successful = TRUE AND confidence >= 0.8;

-- Composite index for cost analysis
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_cost_tracking ON ai_analysis_logs(model_provider, model_name, created_at::date, estimated_cost);

-- View for daily cost analysis
CREATE OR REPLACE VIEW daily_ai_costs AS
SELECT 
    created_at::date as analysis_date,
    model_provider,
    model_name,
    COUNT(*) as analysis_count,
    SUM(tokens_used) as total_tokens,
    SUM(estimated_cost) as total_cost,
    AVG(confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE analysis_successful = FALSE) as failed_count
FROM ai_analysis_logs
GROUP BY created_at::date, model_provider, model_name
ORDER BY analysis_date DESC, total_cost DESC;

-- View for analysis performance metrics
CREATE OR REPLACE VIEW ai_model_performance AS
SELECT 
    model_provider,
    model_name,
    analysis_type,
    COUNT(*) as total_analyses,
    AVG(confidence) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time_ms,
    AVG(tokens_used) as avg_tokens_used,
    AVG(estimated_cost) as avg_cost_per_analysis,
    COUNT(*) FILTER (WHERE analysis_successful = FALSE) as failure_count,
    (COUNT(*) FILTER (WHERE analysis_successful = FALSE) * 100.0 / COUNT(*)) as failure_rate_percent
FROM ai_analysis_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY model_provider, model_name, analysis_type
ORDER BY total_analyses DESC;

-- View for recent user-initiated analyses
CREATE OR REPLACE VIEW recent_test_analyses AS
SELECT 
    id,
    image_id,
    image_url,
    camera_name,
    analysis_type,
    model_provider,
    model_name,
    confidence,
    processing_time_ms,
    tokens_used,
    estimated_cost,
    session_id,
    created_at
FROM ai_analysis_logs
WHERE user_initiated = TRUE
ORDER BY created_at DESC
LIMIT 100;

-- Function to calculate cost based on model and tokens (updated with 2024 official pricing)
CREATE OR REPLACE FUNCTION calculate_ai_cost(
    provider TEXT,
    model TEXT,
    tokens INTEGER
) RETURNS DECIMAL(10, 6) AS $$
BEGIN
    -- OpenAI pricing (average of input/output per 1K tokens, 2024 official rates)
    IF provider = 'openai' THEN
        CASE model
            WHEN 'gpt-4o' THEN RETURN (tokens / 1000.0) * 0.010; -- $5.00 input + $15.00 output avg = $10.00/1M
            WHEN 'gpt-4o-mini' THEN RETURN (tokens / 1000.0) * 0.000375; -- $0.15 input + $0.60 output avg = $0.375/1M
            WHEN 'gpt-4-turbo' THEN RETURN (tokens / 1000.0) * 0.03; -- Legacy pricing
            WHEN 'gpt-4-vision-preview' THEN RETURN (tokens / 1000.0) * 0.03; -- Legacy pricing
            ELSE RETURN (tokens / 1000.0) * 0.02; -- Default OpenAI rate
        END CASE;
    END IF;
    
    -- Google Gemini pricing (2024 official rates)
    IF provider = 'gemini' THEN
        CASE model
            WHEN 'gemini-1.5-flash' THEN RETURN (tokens / 1000.0) * 0.00025; -- $0.10 input + $0.40 output avg = $0.25/1M
            WHEN 'gemini-2.0-flash-exp' THEN RETURN 0; -- Free during preview
            WHEN 'gemini-2.5-pro' THEN RETURN (tokens / 1000.0) * 0.005625; -- $1.25 input + $10.00 output avg = $5.625/1M
            WHEN 'gemini-1.5-pro' THEN RETURN (tokens / 1000.0) * 0.00125; -- Legacy pricing
            ELSE RETURN (tokens / 1000.0) * 0.001; -- Default Gemini rate
        END CASE;
    END IF;
    
    -- Anthropic pricing
    IF provider = 'anthropic' THEN
        RETURN (tokens / 1000.0) * 0.025; -- $25/1M tokens average
    END IF;
    
    -- Default fallback
    RETURN (tokens / 1000.0) * 0.02;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically calculate cost on insert/update
CREATE OR REPLACE FUNCTION set_ai_analysis_cost()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tokens_used IS NOT NULL AND NEW.tokens_used > 0 THEN
        NEW.estimated_cost = calculate_ai_cost(NEW.model_provider, NEW.model_name, NEW.tokens_used);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_ai_analysis_cost
    BEFORE INSERT OR UPDATE ON ai_analysis_logs
    FOR EACH ROW
    EXECUTE FUNCTION set_ai_analysis_cost();

-- Add comment to table
COMMENT ON TABLE ai_analysis_logs IS 'Comprehensive logging of all AI analysis requests and responses for audit trail and cost tracking';