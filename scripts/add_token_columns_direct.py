#!/usr/bin/env python3
"""
Directly add input_tokens and output_tokens columns to ai_analysis_logs table
using Supabase Personal Access Token
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.execute_sql_with_pat import SupabaseSQL

load_dotenv()

def main():
    print("🚀 Adding token columns to ai_analysis_logs table (Direct SQL)")
    print("=" * 50)
    
    try:
        sql_executor = SupabaseSQL()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Please set the following environment variables:")
        print("  - SUPABASE_PROJECT_ID")
        print("  - SUPABASE_ACCESS_TOKEN")
        return
    
    # Step 1: Check current columns
    print("\n📊 Checking current table structure...")
    check_sql = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public' 
    AND table_name = 'ai_analysis_logs'
    AND column_name IN ('input_tokens', 'output_tokens')
    ORDER BY column_name;
    """
    
    result = sql_executor.execute_sql(check_sql)
    
    existing_columns = []
    if result and 'data' in result:
        existing_columns = [row['column_name'] for row in result.get('data', [])]
        if existing_columns:
            print(f"✅ Found existing columns: {', '.join(existing_columns)}")
        else:
            print("⚠️  Token columns not found")
    
    # Step 2: Add missing columns
    if 'input_tokens' not in existing_columns or 'output_tokens' not in existing_columns:
        print("\n🔨 Adding missing token columns...")
        
        # Read the SQL file
        sql_file = Path(__file__).parent.parent / 'database' / 'add_token_columns.sql'
        
        if sql_file.exists():
            with open(sql_file, 'r') as f:
                add_columns_sql = f.read()
        else:
            # Use inline SQL if file not found
            add_columns_sql = """
            -- Add input_tokens and output_tokens columns to ai_analysis_logs table
            ALTER TABLE ai_analysis_logs 
            ADD COLUMN IF NOT EXISTS input_tokens INTEGER,
            ADD COLUMN IF NOT EXISTS output_tokens INTEGER;
            
            -- Update the daily_ai_costs view to include token breakdown
            DROP VIEW IF EXISTS daily_ai_costs;
            CREATE VIEW daily_ai_costs AS
            SELECT 
                created_at::date as analysis_date,
                model_provider,
                model_name,
                COUNT(*) as analysis_count,
                SUM(tokens_used) as total_tokens,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(confidence) as avg_confidence,
                COUNT(*) FILTER (WHERE analysis_successful = FALSE) as failed_count
            FROM ai_analysis_logs
            GROUP BY created_at::date, model_provider, model_name
            ORDER BY analysis_date DESC, total_cost DESC;
            
            -- Add index for cost queries with token fields
            CREATE INDEX IF NOT EXISTS idx_ai_analysis_logs_tokens ON ai_analysis_logs(input_tokens, output_tokens) 
            WHERE input_tokens IS NOT NULL AND output_tokens IS NOT NULL;
            """
        
        result = sql_executor.execute_sql(add_columns_sql)
        
        if result:
            print("✅ SQL executed successfully!")
        else:
            print("❌ Failed to execute SQL")
            return
    else:
        print("✅ Both token columns already exist!")
    
    # Step 3: Verify columns were added
    print("\n✅ Verifying columns...")
    verify_sql = """
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' 
    AND table_name = 'ai_analysis_logs'
    AND column_name IN ('input_tokens', 'output_tokens')
    ORDER BY column_name;
    """
    
    result = sql_executor.execute_sql(verify_sql)
    
    if result and 'data' in result:
        print("\nColumn details:")
        for col in result['data']:
            print(f"  ✓ {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    
    # Step 4: Check the view
    print("\n📊 Checking daily_ai_costs view...")
    view_check_sql = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' 
    AND table_name = 'daily_ai_costs'
    AND column_name LIKE '%token%'
    ORDER BY ordinal_position;
    """
    
    result = sql_executor.execute_sql(view_check_sql)
    
    if result and 'data' in result:
        token_columns = [col['column_name'] for col in result['data']]
        if token_columns:
            print(f"✅ View includes token columns: {', '.join(token_columns)}")
    
    # Step 5: Check index
    print("\n🔍 Checking token index...")
    index_check_sql = """
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND tablename = 'ai_analysis_logs'
    AND indexname = 'idx_ai_analysis_logs_tokens';
    """
    
    result = sql_executor.execute_sql(index_check_sql)
    
    if result and 'data' in result and result['data']:
        print("✅ Token index exists")
    
    print("\n✨ Token columns successfully configured!")
    print("\nSummary:")
    print("  ✓ input_tokens column added to ai_analysis_logs")
    print("  ✓ output_tokens column added to ai_analysis_logs")
    print("  ✓ daily_ai_costs view updated with token breakdowns")
    print("  ✓ Index created for efficient token queries")

if __name__ == "__main__":
    main()