#!/usr/bin/env python3
"""
Execute database migration to add quality rating and user notes columns
"""
import os
import sys
from dotenv import load_dotenv
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def run_migration():
    """Execute the migration SQL using Supabase REST API"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment")
        return False
    
    # SQL statements to execute
    sql_statements = [
        """
        ALTER TABLE ai_analysis_logs 
        ADD COLUMN IF NOT EXISTS quality_rating INTEGER 
        CHECK (quality_rating >= 1 AND quality_rating <= 5)
        """,
        """
        ALTER TABLE ai_analysis_logs 
        ADD COLUMN IF NOT EXISTS user_notes TEXT
        """,
        """
        ALTER TABLE ai_analysis_logs 
        ADD COLUMN IF NOT EXISTS notes_updated_at TIMESTAMP WITH TIME ZONE
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_quality_rating 
        ON ai_analysis_logs(quality_rating)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_notes_updated 
        ON ai_analysis_logs(notes_updated_at)
        """,
        """
        COMMENT ON COLUMN ai_analysis_logs.quality_rating IS 'User rating of analysis quality (1-5 stars)'
        """,
        """
        COMMENT ON COLUMN ai_analysis_logs.user_notes IS 'User notes about the analysis'
        """,
        """
        COMMENT ON COLUMN ai_analysis_logs.notes_updated_at IS 'Timestamp of last note/rating update'
        """
    ]
    
    # Execute each statement using Supabase REST API
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    print("Running migration to add quality_rating and user_notes columns...")
    
    success_count = 0
    for i, sql in enumerate(sql_statements, 1):
        print(f"\nExecuting statement {i}/{len(sql_statements)}...")
        print(f"SQL: {sql.strip()[:80]}...")
        
        # Use the Supabase REST API to execute SQL
        # Note: Direct SQL execution requires using the pg_net extension or admin API
        # For now, we'll use the Supabase client approach
        
        # Since direct SQL execution via REST API is limited, we'll use the 
        # Supabase Python client approach
        try:
            from src.db.supabase_client import SupabaseClient
            
            supabase = SupabaseClient(
                url=supabase_url,
                key=supabase_key
            )
            
            # Check if columns already exist by trying to query them
            if i <= 3:  # For ALTER TABLE statements
                try:
                    # Test if column exists by selecting it
                    column_name = 'quality_rating' if i == 1 else 'user_notes' if i == 2 else 'notes_updated_at'
                    test_query = supabase.client.table('ai_analysis_logs').select(column_name).limit(1).execute()
                    print(f"Column {column_name} already exists, skipping...")
                    success_count += 1
                    continue
                except Exception as e:
                    # Column doesn't exist, proceed with creation
                    print(f"Column doesn't exist yet, will be created by migration")
            
            # For actual migration, you need to run these in Supabase SQL editor
            print(f"Statement {i} needs to be run in Supabase SQL editor")
            success_count += 1
            
        except Exception as e:
            print(f"Error with statement {i}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Migration preparation complete: {success_count}/{len(sql_statements)} statements ready")
    print(f"\nIMPORTANT: Please run the following SQL in your Supabase SQL editor:")
    print(f"{'='*60}\n")
    
    # Output full SQL for manual execution
    full_sql = ";\n\n".join(sql.strip() for sql in sql_statements) + ";"
    print(full_sql)
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)