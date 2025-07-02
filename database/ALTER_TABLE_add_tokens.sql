-- RUN THIS IN SUPABASE SQL EDITOR TO ADD MISSING COLUMNS
-- This adds the input_tokens and output_tokens columns that are needed for cost tracking

ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS input_tokens INTEGER;

ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS output_tokens INTEGER;

-- Verify the columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ai_analysis_logs' 
AND column_name IN ('input_tokens', 'output_tokens', 'estimated_cost', 'tokens_used');