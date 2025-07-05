-- Migration: Add quality rating and user notes to ai_analysis_logs table
-- Run this migration to add user feedback columns to the analysis logs

-- Add quality_rating column (1-5 stars)
ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS quality_rating INTEGER 
CHECK (quality_rating >= 1 AND quality_rating <= 5);

-- Add user_notes column for text notes
ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS user_notes TEXT;

-- Add timestamp for when notes were last updated
ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS notes_updated_at TIMESTAMP WITH TIME ZONE;

-- Create index on quality_rating for filtering
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_quality_rating 
ON ai_analysis_logs(quality_rating);

-- Create index on notes_updated_at for sorting by recent edits
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_notes_updated 
ON ai_analysis_logs(notes_updated_at);

COMMENT ON COLUMN ai_analysis_logs.quality_rating IS 'User rating of analysis quality (1-5 stars)';
COMMENT ON COLUMN ai_analysis_logs.user_notes IS 'User notes about the analysis';
COMMENT ON COLUMN ai_analysis_logs.notes_updated_at IS 'Timestamp of last note/rating update';