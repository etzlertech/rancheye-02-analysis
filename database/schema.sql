-- RanchEye-02-Analysis Database Schema
-- This service reads from spypoint_images (created by rancheye-01)
-- and writes analysis results to its own tables

-- Analysis configuration table
-- Defines what types of analysis to run on which cameras
CREATE TABLE IF NOT EXISTS analysis_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    camera_name TEXT,  -- NULL means apply to all cameras
    analysis_type TEXT NOT NULL, -- 'gate_detection', 'water_level', 'animal_detection', 'custom'
    model_provider TEXT NOT NULL, -- 'openai', 'anthropic', 'gemini'
    model_name TEXT NOT NULL, -- 'gpt-4-vision', 'claude-3-opus', etc.
    prompt_template TEXT NOT NULL,
    threshold FLOAT DEFAULT 0.8, -- Confidence threshold for alerts
    alert_cooldown_minutes INTEGER DEFAULT 60, -- Prevent alert spam
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis results table
-- Stores the output from AI analysis
CREATE TABLE IF NOT EXISTS image_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id TEXT REFERENCES spypoint_images(image_id),
    config_id UUID REFERENCES analysis_configs(id),
    model_provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    result JSONB NOT NULL, -- Structured results from AI
    confidence FLOAT, -- Overall confidence score
    alert_triggered BOOLEAN DEFAULT false,
    processing_time_ms INTEGER,
    tokens_used INTEGER, -- For cost tracking
    error TEXT, -- If analysis failed
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis queue/tasks table
-- Manages pending analysis jobs
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id TEXT REFERENCES spypoint_images(image_id),
    config_id UUID REFERENCES analysis_configs(id),
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    priority INTEGER DEFAULT 5, -- 1-10, higher = more urgent
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    UNIQUE(image_id, config_id) -- Prevent duplicate tasks
);

-- Alerts table
-- Tracks alerts that have been triggered
CREATE TABLE IF NOT EXISTS analysis_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_result_id UUID REFERENCES image_analysis_results(id),
    alert_type TEXT NOT NULL, -- 'immediate', 'digest', 'trend'
    severity TEXT NOT NULL, -- 'critical', 'warning', 'info'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    camera_name TEXT NOT NULL,
    image_url TEXT,
    alert_data JSONB, -- Additional context
    sent_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis cache table
-- Caches results for similar images to reduce API costs
CREATE TABLE IF NOT EXISTS analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_hash TEXT NOT NULL, -- Perceptual hash of image
    analysis_type TEXT NOT NULL,
    model_provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    result JSONB NOT NULL,
    confidence FLOAT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(image_hash, analysis_type, model_provider, model_name)
);

-- Cost tracking table
-- Monitor API usage and costs
CREATE TABLE IF NOT EXISTS analysis_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    model_provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    analysis_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, model_provider, model_name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_analysis_results_image ON image_analysis_results(image_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_created ON image_analysis_results(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_results_alert ON image_analysis_results(alert_triggered) WHERE alert_triggered = true;

CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_scheduled ON analysis_tasks(scheduled_at) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_analysis_alerts_created ON analysis_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_alerts_sent ON analysis_alerts(sent_at) WHERE sent_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_analysis_cache_lookup ON analysis_cache(image_hash, analysis_type, model_provider, model_name);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_expires ON analysis_cache(expires_at);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_analysis_configs_updated_at BEFORE UPDATE ON analysis_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analysis_costs_updated_at BEFORE UPDATE ON analysis_costs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample analysis configurations
-- Uncomment and modify to create default configs

/*
-- Gate Detection Config
INSERT INTO analysis_configs (name, analysis_type, model_provider, model_name, prompt_template, threshold) VALUES
('Main Gate Monitor', 'gate_detection', 'openai', 'gpt-4-vision-preview', 
'Analyze this trail camera image and determine if a gate is visible. If a gate is visible, determine if it is OPEN or CLOSED. Respond with a JSON object containing: {"gate_visible": boolean, "gate_open": boolean, "confidence": float between 0-1, "reasoning": "brief explanation"}', 
0.85);

-- Water Level Config
INSERT INTO analysis_configs (name, analysis_type, model_provider, model_name, prompt_template, threshold) VALUES
('Water Trough Monitor', 'water_level', 'openai', 'gpt-4-vision-preview',
'Analyze this trail camera image for water troughs or containers. Estimate the water level as: FULL (80-100%), ADEQUATE (40-80%), LOW (10-40%), or EMPTY (0-10%). Respond with JSON: {"water_visible": boolean, "water_level": "FULL|ADEQUATE|LOW|EMPTY", "percentage_estimate": number, "confidence": float, "reasoning": "explanation"}',
0.80);

-- Animal Detection Config
INSERT INTO analysis_configs (name, analysis_type, model_provider, model_name, prompt_template, threshold) VALUES
('Wildlife Monitor', 'animal_detection', 'anthropic', 'claude-3-opus-20240229',
'Analyze this trail camera image for any animals. Identify the species if possible, count how many, and note if they are livestock or wildlife. Respond with JSON: {"animals_detected": boolean, "animals": [{"species": "name or unknown", "count": number, "type": "livestock|wildlife|unknown", "confidence": float}], "reasoning": "explanation"}',
0.75);
*/

-- Function to create analysis tasks for new images
CREATE OR REPLACE FUNCTION create_analysis_tasks_for_image(p_image_id TEXT)
RETURNS void AS $$
DECLARE
    config record;
    camera_name TEXT;
BEGIN
    -- Get camera name for this image
    SELECT si.camera_name INTO camera_name 
    FROM spypoint_images si 
    WHERE si.image_id = p_image_id;
    
    -- Create tasks for all active configs that apply to this camera
    FOR config IN 
        SELECT * FROM analysis_configs 
        WHERE active = true 
        AND (camera_name IS NULL OR camera_name = camera_name)
    LOOP
        INSERT INTO analysis_tasks (image_id, config_id, priority)
        VALUES (p_image_id, config.id, 5)
        ON CONFLICT (image_id, config_id) DO NOTHING;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- View for monitoring analysis performance
CREATE OR REPLACE VIEW analysis_performance AS
SELECT 
    ar.model_provider,
    ar.model_name,
    ar.analysis_type,
    COUNT(*) as total_analyses,
    AVG(ar.processing_time_ms) as avg_processing_time_ms,
    AVG(ar.confidence) as avg_confidence,
    SUM(CASE WHEN ar.alert_triggered THEN 1 ELSE 0 END) as alerts_triggered,
    SUM(ar.tokens_used) as total_tokens,
    MAX(ar.created_at) as last_analysis
FROM image_analysis_results ar
WHERE ar.created_at > NOW() - INTERVAL '7 days'
GROUP BY ar.model_provider, ar.model_name, ar.analysis_type;

-- View for pending work
CREATE OR REPLACE VIEW pending_analysis_summary AS
SELECT 
    at.status,
    ac.analysis_type,
    COUNT(*) as task_count,
    MIN(at.scheduled_at) as oldest_task,
    AVG(EXTRACT(EPOCH FROM (NOW() - at.scheduled_at))) as avg_age_seconds
FROM analysis_tasks at
JOIN analysis_configs ac ON at.config_id = ac.id
WHERE at.status IN ('pending', 'processing')
GROUP BY at.status, ac.analysis_type;