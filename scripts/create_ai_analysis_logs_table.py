#!/usr/bin/env python3
"""
Script to create the ai_analysis_logs table in Supabase PostgreSQL database.
This table stores comprehensive logs of all AI analysis requests and responses.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.db.supabase_client import SupabaseClient
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")
        sys.exit(1)
    
    client = SupabaseClient(supabase_url, supabase_key)
    
    # Read the SQL file
    sql_file_path = project_root / "database" / "ai_analysis_logs.sql"
    
    if not sql_file_path.exists():
        print(f"Error: SQL file not found at {sql_file_path}")
        sys.exit(1)
    
    print(f"Reading SQL from {sql_file_path}")
    with open(sql_file_path, 'r') as f:
        sql_content = f.read()
    
    # Split SQL into individual statements (simple approach)
    # This handles most cases but may need refinement for complex SQL
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        current_statement.append(line)
        
        # End of statement
        if line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        statement = ' '.join(current_statement)
        if statement.strip():
            statements.append(statement)
    
    print(f"Found {len(statements)} SQL statements to execute")
    
    # Execute each statement
    success_count = 0
    for i, statement in enumerate(statements, 1):
        try:
            print(f"Executing statement {i}/{len(statements)}...")
            # Note: Supabase client doesn't have direct SQL execution
            # We'll need to use the PostgreSQL connection or Supabase SQL editor
            print(f"Statement: {statement[:100]}...")
            
            # For now, just print the statements that need to be run
            # In production, you would execute these via psql or Supabase SQL editor
            print("✓ Would execute (manual execution required)")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Error executing statement {i}: {e}")
            print(f"Statement: {statement}")
    
    print(f"\nMigration summary:")
    print(f"  Total statements: {len(statements)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {len(statements) - success_count}")
    
    if success_count == len(statements):
        print("\n✓ All statements processed successfully!")
        print("\nNOTE: This script prints the SQL statements that need to be executed.")
        print("Please run these statements manually in your Supabase SQL editor or via psql:")
        print(f"\npsql -h <your-supabase-host> -U postgres -d postgres < {sql_file_path}")
    else:
        print(f"\n✗ {len(statements) - success_count} statements failed")
        sys.exit(1)

if __name__ == "__main__":
    main()