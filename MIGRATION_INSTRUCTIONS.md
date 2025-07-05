# Database Migration Instructions

The enhanced analysis history grid requires new database columns. Please follow these steps:

## Step 1: Open Supabase SQL Editor

1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New query"

## Step 2: Run the Migration SQL

Copy and paste the following SQL into the editor and click "Run":

```sql
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

-- Add comments for documentation
COMMENT ON COLUMN ai_analysis_logs.quality_rating IS 'User rating of analysis quality (1-5 stars)';
COMMENT ON COLUMN ai_analysis_logs.user_notes IS 'User notes about the analysis';
COMMENT ON COLUMN ai_analysis_logs.notes_updated_at IS 'Timestamp of last note/rating update';
```

## Step 3: Verify the Migration

After running the SQL, you can verify it worked by running:

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'ai_analysis_logs' 
AND column_name IN ('quality_rating', 'user_notes', 'notes_updated_at')
ORDER BY ordinal_position;
```

You should see three rows showing the new columns.

## Step 4: Test the Feature

1. Refresh your RanchEye dashboard
2. Click "Analysis History" button in the header
3. Expand any image group to see the analysis grid
4. Try rating an analysis (click the stars)
5. Try adding notes to an analysis

## What These Columns Do

- **quality_rating**: Stores your 1-5 star rating for each AI analysis
- **user_notes**: Stores your text notes about the analysis quality
- **notes_updated_at**: Tracks when you last updated the rating or notes

The frontend will automatically save your ratings and notes as you make changes!