#!/usr/bin/env python3
"""
Execute database migration using Supabase Management API
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def execute_migration():
    """Execute the migration using Supabase Management API"""
    
    # Get credentials
    project_ref = os.getenv('SUPABASE_PROJECT_ID')
    access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
    
    if not project_ref or not access_token:
        print("Error: SUPABASE_PROJECT_ID and SUPABASE_ACCESS_TOKEN must be set")
        return False
    
    # Supabase Management API endpoint for running SQL
    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # SQL statements to execute
    sql_statements = [
        """ALTER TABLE ai_analysis_logs 
        ADD COLUMN IF NOT EXISTS quality_rating INTEGER 
        CHECK (quality_rating >= 1 AND quality_rating <= 5)""",
        
        """ALTER TABLE ai_analysis_logs 
        ADD COLUMN IF NOT EXISTS user_notes TEXT""",
        
        """ALTER TABLE ai_analysis_logs 
        ADD COLUMN IF NOT EXISTS notes_updated_at TIMESTAMP WITH TIME ZONE""",
        
        """CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_quality_rating 
        ON ai_analysis_logs(quality_rating)""",
        
        """CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_notes_updated 
        ON ai_analysis_logs(notes_updated_at)""",
        
        """COMMENT ON COLUMN ai_analysis_logs.quality_rating IS 'User rating of analysis quality (1-5 stars)'""",
        
        """COMMENT ON COLUMN ai_analysis_logs.user_notes IS 'User notes about the analysis'""",
        
        """COMMENT ON COLUMN ai_analysis_logs.notes_updated_at IS 'Timestamp of last note/rating update'"""
    ]
    
    print("Executing migration via Supabase Management API...")
    print(f"Project: {project_ref}")
    
    success_count = 0
    for i, sql in enumerate(sql_statements, 1):
        print(f"\nExecuting statement {i}/{len(sql_statements)}...")
        print(f"SQL: {sql[:80]}...")
        
        payload = {
            "query": sql
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print(f"✓ Statement {i} executed successfully")
                success_count += 1
            else:
                print(f"✗ Statement {i} failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"✗ Error executing statement {i}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Migration complete: {success_count}/{len(sql_statements)} statements executed successfully")
    
    # Verify the migration
    if success_count == len(sql_statements):
        print("\n✅ All migration statements executed successfully!")
        print("The new columns (quality_rating, user_notes, notes_updated_at) should now be available.")
        return True
    else:
        print("\n⚠️  Some statements failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)