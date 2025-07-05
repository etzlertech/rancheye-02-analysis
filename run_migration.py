#!/usr/bin/env python3
"""
Run database migration to add quality rating and user notes columns
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.supabase_client import SupabaseClient

load_dotenv()

def run_migration():
    """Execute the migration SQL"""
    # Initialize Supabase client
    supabase = SupabaseClient(
        url=os.getenv('SUPABASE_URL'),
        key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    )
    
    # Read migration SQL
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', 'add_rating_notes_columns.sql')
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    try:
        # Execute migration
        print("Running migration to add quality_rating and user_notes columns...")
        
        # Split SQL into individual statements and execute
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            print(f"Executing: {statement[:50]}...")
            # Note: Supabase Python client doesn't have direct SQL execution
            # You'll need to run this via Supabase dashboard SQL editor
            print("Please run this statement in Supabase SQL editor:")
            print(statement)
            print("-" * 50)
        
        print("\nMigration SQL has been generated. Please run these statements in your Supabase SQL editor.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)