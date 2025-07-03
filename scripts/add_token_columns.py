#!/usr/bin/env python3
"""
Add input_tokens and output_tokens columns to ai_analysis_logs table
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.supabase_client import SupabaseClient
from supabase import create_client, Client

load_dotenv()

def main():
    print("🚀 Adding token columns to ai_analysis_logs table")
    print("=" * 50)
    
    # Get credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Missing SUPABASE_URL or SUPABASE_ANON_KEY")
        return
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Step 1: Check current table structure
    print("\n📊 Checking current table structure...")
    try:
        # Get column information
        check_columns_sql = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = 'ai_analysis_logs'
        ORDER BY ordinal_position;
        """
        
        # Execute raw SQL using RPC if available, otherwise use a workaround
        # Since Supabase Python client doesn't have direct SQL execution, we'll check via a select
        result = supabase.table('ai_analysis_logs').select('*').limit(0).execute()
        
        print("✅ Table exists!")
        
        # Check if we can see the columns by trying to select them
        has_input_tokens = False
        has_output_tokens = False
        
        try:
            # Try to select the columns to see if they exist
            test_query = supabase.table('ai_analysis_logs').select('input_tokens,output_tokens').limit(1).execute()
            has_input_tokens = True
            has_output_tokens = True
            print("✅ Both token columns already exist!")
        except Exception as e:
            # One or both columns don't exist
            print("⚠️  One or both token columns don't exist yet")
    
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        return
    
    # Step 2: Read and execute the SQL file if columns don't exist
    if not has_input_tokens or not has_output_tokens:
        print("\n🔨 Adding missing columns...")
        
        # Read the SQL file
        sql_file = Path(__file__).parent.parent / 'database' / 'add_token_columns.sql'
        
        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        print(f"📄 Read SQL from: {sql_file}")
        
        # Since Supabase Python client doesn't support direct SQL execution,
        # we need to use the REST API or Management API
        # For now, let's use the execute_sql_with_pat.py approach
        
        print("\n⚠️  Note: The Supabase Python client doesn't support direct SQL execution.")
        print("Please run the following command to execute the SQL:")
        print(f"\n  psql {supabase_url.replace('https://', 'postgresql://postgres:your-password@').replace('.supabase.co', '.supabase.co:5432/postgres')} < {sql_file}")
        print("\nOr use the Supabase dashboard SQL editor to run the contents of:")
        print(f"  {sql_file}")
        
        # Alternative: Try using the management API if we have a personal access token
        pat = os.getenv('SUPABASE_ACCESS_TOKEN')
        project_id = os.getenv('SUPABASE_PROJECT_ID')
        
        if pat and project_id:
            print("\n🔑 Found Personal Access Token, attempting to execute SQL...")
            
            # Import and use the SQL executor
            from execute_sql_with_pat import SupabaseSQL
            
            sql_executor = SupabaseSQL()
            result = sql_executor.execute_sql(sql_content)
            
            if result:
                print("✅ SQL executed successfully!")
            else:
                print("❌ Failed to execute SQL")
                return
        else:
            print("\n💡 Tip: Set SUPABASE_ACCESS_TOKEN and SUPABASE_PROJECT_ID to execute SQL automatically")
            return
    
    # Step 3: Verify columns were added
    print("\n✅ Verifying columns...")
    try:
        # Try to select the columns again
        verify_query = supabase.table('ai_analysis_logs').select('input_tokens,output_tokens').limit(1).execute()
        print("✅ Both token columns are now available!")
        
        # Test inserting a record with token values
        print("\n🧪 Testing column functionality...")
        test_data = {
            'image_id': 'test-image-123',
            'analysis_type': 'test',
            'prompt_text': 'Test prompt',
            'custom_prompt': False,
            'model_provider': 'openai',
            'model_name': 'gpt-4',
            'raw_response': 'Test response',
            'analysis_successful': True,
            'tokens_used': 150,
            'input_tokens': 100,
            'output_tokens': 50,
            'estimated_cost': 0.005
        }
        
        # Try to insert (we'll delete it right after)
        insert_result = supabase.table('ai_analysis_logs').insert(test_data).execute()
        
        if insert_result.data:
            print("✅ Successfully inserted test record with token values!")
            
            # Clean up test record
            test_id = insert_result.data[0]['id']
            supabase.table('ai_analysis_logs').delete().eq('id', test_id).execute()
            print("🧹 Cleaned up test record")
        
    except Exception as e:
        print(f"❌ Error verifying columns: {e}")
        return
    
    print("\n✨ Token columns successfully added to ai_analysis_logs table!")
    print("\nThe following columns are now available:")
    print("  - input_tokens (INTEGER)")
    print("  - output_tokens (INTEGER)")
    print("\nThe daily_ai_costs view has also been updated to include token breakdowns.")

if __name__ == "__main__":
    main()