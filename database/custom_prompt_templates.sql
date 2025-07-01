-- Custom Prompt Templates Storage
-- Allows users to save and manage custom analysis prompts

CREATE TABLE IF NOT EXISTS custom_prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template Information
    name TEXT NOT NULL, -- User-defined name for the template
    description TEXT, -- Optional description of what this template analyzes
    
    -- Template Content
    prompt_text TEXT NOT NULL, -- The actual prompt content
    analysis_type TEXT NOT NULL, -- 'gate_detection', 'door_detection', 'custom', etc.
    
    -- Template Properties
    is_default BOOLEAN DEFAULT FALSE, -- Whether this is the default for its analysis_type
    is_system BOOLEAN DEFAULT FALSE, -- System templates vs user-created
    created_by TEXT DEFAULT 'web_user', -- Who created this template
    
    -- Usage Statistics
    usage_count INTEGER DEFAULT 0, -- How many times this template has been used
    last_used_at TIMESTAMPTZ, -- When it was last used
    
    -- Template Metadata
    tags TEXT[], -- Optional tags for categorization
    model_optimized_for TEXT[], -- Which models this prompt works best with
    expected_output_format TEXT DEFAULT 'json', -- 'json', 'text', 'structured'
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_default_per_analysis_type UNIQUE (analysis_type, is_default) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT valid_analysis_type CHECK (analysis_type IN ('gate_detection', 'door_detection', 'water_level', 'feed_bin_status', 'animal_detection', 'custom'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_custom_prompts_analysis_type ON custom_prompt_templates(analysis_type);
CREATE INDEX IF NOT EXISTS idx_custom_prompts_is_default ON custom_prompt_templates(is_default) WHERE is_default = TRUE;
CREATE INDEX IF NOT EXISTS idx_custom_prompts_created_by ON custom_prompt_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_custom_prompts_usage ON custom_prompt_templates(usage_count DESC, last_used_at DESC);
CREATE INDEX IF NOT EXISTS idx_custom_prompts_tags ON custom_prompt_templates USING GIN(tags);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_custom_prompt_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_custom_prompt_updated_at
    BEFORE UPDATE ON custom_prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_custom_prompt_updated_at();

-- Function to increment usage count
CREATE OR REPLACE FUNCTION increment_prompt_usage(template_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE custom_prompt_templates 
    SET 
        usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE id = template_id;
END;
$$ LANGUAGE plpgsql;

-- Function to set default template (ensures only one default per analysis type)
CREATE OR REPLACE FUNCTION set_default_template(template_id UUID)
RETURNS VOID AS $$
DECLARE
    template_analysis_type TEXT;
BEGIN
    -- Get the analysis type of the template being set as default
    SELECT analysis_type INTO template_analysis_type 
    FROM custom_prompt_templates 
    WHERE id = template_id;
    
    -- Remove default status from all templates of this analysis type
    UPDATE custom_prompt_templates 
    SET is_default = FALSE 
    WHERE analysis_type = template_analysis_type;
    
    -- Set the specified template as default
    UPDATE custom_prompt_templates 
    SET is_default = TRUE 
    WHERE id = template_id;
END;
$$ LANGUAGE plpgsql;

-- View for active templates with usage stats
CREATE OR REPLACE VIEW active_prompt_templates AS
SELECT 
    id,
    name,
    description,
    analysis_type,
    is_default,
    is_system,
    created_by,
    usage_count,
    last_used_at,
    created_at,
    updated_at,
    CASE 
        WHEN last_used_at IS NULL THEN 'never'
        WHEN last_used_at > NOW() - INTERVAL '7 days' THEN 'recent'
        WHEN last_used_at > NOW() - INTERVAL '30 days' THEN 'active'
        ELSE 'inactive'
    END as usage_status,
    char_length(prompt_text) as prompt_length
FROM custom_prompt_templates
ORDER BY analysis_type, is_default DESC, usage_count DESC;

-- Insert default system templates based on existing prompts
INSERT INTO custom_prompt_templates (name, description, prompt_text, analysis_type, is_default, is_system) VALUES
(
    'Default Gate Detection',
    'Standard gate detection analysis for ranch cameras',
    'You are analyzing a trail camera image from a ranch. Look for any gates in the image and determine their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "gate_visible": true or false,
  "gate_open": true or false (null if no gate visible),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of what you see in the image and why you made this decision",
  "visual_evidence": "Specific visual details that support your conclusion (e.g., gate posts, hinges, gaps, shadows)"
}',
    'gate_detection',
    TRUE,
    TRUE
),
(
    'Default Door Detection',
    'Standard door detection analysis with opening percentage',
    'You are analyzing a trail camera image from a ranch or building. Look for any doors in the image and determine their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "door_visible": true or false,
  "door_open": true or false (null if no door visible),
  "opening_percentage": 0 to 100 (estimated percentage the door is open, 0=fully closed, 100=fully open, null if not visible),
  "door_type": "barn door" or "regular door" or "sliding door" or "garage door" or "other" (null if not visible),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of what you see and how you determined the door status",
  "visual_evidence": "Specific visual details like door frame, hinges, opening gap, shadows, interior visibility"
}',
    'door_detection',
    TRUE,
    TRUE
),
(
    'Default Water Level',
    'Standard water level assessment for troughs and tanks',
    'You are analyzing a trail camera image from a ranch. Look for water troughs, tanks, or containers and assess the water level.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "water_visible": true or false,
  "water_level": "FULL" or "ADEQUATE" or "LOW" or "EMPTY" (null if no water container visible),
  "percentage_estimate": 0 to 100 (null if not applicable),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of your water level assessment",
  "visual_evidence": "Specific details about water color, reflections, container fill line, or moisture marks"
}',
    'water_level',
    TRUE,
    TRUE
),
(
    'Default Animal Detection',
    'Standard animal identification and behavior analysis',
    'You are analyzing a trail camera image from a ranch. Identify any animals in the image.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "animals_detected": true or false,
  "animals": [
    {
      "species": "specific animal name",
      "count": number of this species visible,
      "type": "livestock" or "wildlife",
      "confidence": 0.0 to 1.0,
      "location": "where in the image (e.g., left foreground, center background)",
      "behavior": "what the animal is doing (e.g., grazing, walking, resting)"
    }
  ],
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of how you identified each animal",
  "visual_evidence": "Specific features used for identification (e.g., body shape, coloring, size)"
}',
    'animal_detection',
    TRUE,
    TRUE
),
(
    'Default Feed Bin Status',
    'Standard feed bin and feeder level assessment',
    'You are analyzing a trail camera image from a ranch. Look for feed bins, feeders, or hay storage and assess their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "feeder_visible": true or false,
  "feed_level": "FULL" or "ADEQUATE" or "LOW" or "EMPTY" (null if no feeder visible),
  "percentage_estimate": 0 to 100 (null if not applicable),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of your feed level assessment",
  "visual_evidence": "Specific details about feed visibility, bin shadows, or fill indicators",
  "concerns": "Any maintenance issues, damage, or other concerns noticed (null if none)"
}',
    'feed_bin_status',
    TRUE,
    TRUE
)
ON CONFLICT (analysis_type, is_default) DO NOTHING;

-- Add comment to table
COMMENT ON TABLE custom_prompt_templates IS 'Storage for user-defined and system prompt templates with versioning and usage tracking';