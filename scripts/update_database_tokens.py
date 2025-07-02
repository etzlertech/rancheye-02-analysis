#!/usr/bin/env python3
"""
Script to update the database schema to add token tracking columns
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def update_database_schema():
    """Add input_tokens and output_tokens columns to ai_analysis_logs"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        return False
    
    supabase: Client = create_client(url, key)
    
    # Read the SQL file
    sql_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'add_token_columns.sql')
    with open(sql_file, 'r') as f:
        sql_commands = f.read()
    
    try:
        # Execute the SQL commands
        # Note: Supabase Python client doesn't have a direct SQL execution method
        # We'll use the REST API directly
        import requests
        
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        # Split commands and execute each one
        commands = sql_commands.split(';')
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
                
            print(f"Executing: {cmd[:50]}...")
            
            # Use Supabase's SQL endpoint
            response = requests.post(
                f"{url}/rest/v1/rpc/query",
                headers=headers,
                json={"query": cmd}
            )
            
            if response.status_code != 200:
                # Try alternative approach - direct SQL execution
                # This might not work depending on Supabase setup
                print(f"Note: Command might need to be run manually: {cmd[:50]}...")
        
        print("\nDatabase schema update attempted.")
        print("\nIMPORTANT: If the update failed, please run the following SQL manually in Supabase SQL Editor:")
        print("-" * 80)
        print(sql_commands)
        print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"Error updating schema: {e}")
        print("\nPlease run the SQL manually in Supabase SQL Editor:")
        print("-" * 80)
        print(sql_commands)
        print("-" * 80)
        return False

if __name__ == "__main__":
    print("Updating database schema to add token tracking columns...")
    if update_database_schema():
        print("Schema update process completed.")
    else:
        print("Schema update failed - please run SQL manually.")