#!/usr/bin/env python3
"""
Execute migration using direct PostgreSQL connection via Supabase
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

load_dotenv()

def get_db_connection():
    """Create direct PostgreSQL connection to Supabase"""
    # Parse Supabase URL to get database connection details
    supabase_url = os.getenv('SUPABASE_URL')
    project_id = os.getenv('SUPABASE_PROJECT_ID')
    
    # Supabase PostgreSQL connection string format
    # Host: db.<project-ref>.supabase.co
    # Port: 5432 (default PostgreSQL port) or 6543 (pooler)
    # Database: postgres
    # Password: from SUPABASE_SERVICE_ROLE_KEY or database password
    
    # For Supabase, we need to construct the database URL
    db_host = f"db.{project_id}.supabase.co"
    db_name = "postgres"
    db_user = "postgres"
    db_password = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Sometimes this works
    
    # Alternative: Try using the JWT secret as password
    if not db_password:
        db_password = os.getenv('SUPABASE_JWT_SECRET')
    
    try:
        # Try direct connection
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=5432,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"Direct connection failed: {e}")
        # Try pooler connection
        try:
            conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                port=6543,  # Pooler port
                sslmode='require'
            )
            return conn
        except Exception as e2:
            print(f"Pooler connection also failed: {e2}")
            return None

def execute_migration():
    """Execute the migration SQL statements"""
    
    # First, let's try using the Supabase client to check existing columns
    from src.db.supabase_client import SupabaseClient
    
    supabase = SupabaseClient(
        url=os.getenv('SUPABASE_URL'),
        key=os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    print("Checking if columns already exist...")
    
    # Check each column
    columns_to_check = ['quality_rating', 'user_notes', 'notes_updated_at']
    existing_columns = []
    
    for column in columns_to_check:
        try:
            # Try to select the column
            response = supabase.client.table('ai_analysis_logs').select(f'id, {column}').limit(1).execute()
            print(f"✓ Column '{column}' already exists")
            existing_columns.append(column)
        except Exception as e:
            if '42703' in str(e):  # Column doesn't exist error code
                print(f"✗ Column '{column}' does not exist")
            else:
                print(f"? Error checking column '{column}': {e}")
    
    if len(existing_columns) == len(columns_to_check):
        print("\n✅ All columns already exist! Migration is complete.")
        return True
    
    print(f"\n⚠️ Need to create {len(columns_to_check) - len(existing_columns)} columns")
    print("\nAttempting direct PostgreSQL connection...")
    
    conn = get_db_connection()
    if not conn:
        print("\n❌ Could not establish database connection")
        print("\nPlease run the following SQL in your Supabase dashboard:")
        print("="*60)
        print("""
-- Add columns if they don't exist
ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS quality_rating INTEGER 
CHECK (quality_rating >= 1 AND quality_rating <= 5);

ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS user_notes TEXT;

ALTER TABLE ai_analysis_logs 
ADD COLUMN IF NOT EXISTS notes_updated_at TIMESTAMP WITH TIME ZONE;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_quality_rating 
ON ai_analysis_logs(quality_rating);

CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_notes_updated 
ON ai_analysis_logs(notes_updated_at);
        """)
        return False
    
    # If we have a connection, execute the migration
    cursor = conn.cursor()
    
    sql_statements = [
        "ALTER TABLE ai_analysis_logs ADD COLUMN IF NOT EXISTS quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5)",
        "ALTER TABLE ai_analysis_logs ADD COLUMN IF NOT EXISTS user_notes TEXT",
        "ALTER TABLE ai_analysis_logs ADD COLUMN IF NOT EXISTS notes_updated_at TIMESTAMP WITH TIME ZONE",
        "CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_quality_rating ON ai_analysis_logs(quality_rating)",
        "CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_notes_updated ON ai_analysis_logs(notes_updated_at)"
    ]
    
    success_count = 0
    for i, sql in enumerate(sql_statements, 1):
        try:
            print(f"\nExecuting: {sql[:60]}...")
            cursor.execute(sql)
            conn.commit()
            print("✓ Success")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Migration complete: {success_count}/{len(sql_statements)} statements executed")
    
    return success_count == len(sql_statements)

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)