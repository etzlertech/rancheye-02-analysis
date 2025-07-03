#!/usr/bin/env python3
"""
Check if ai_analysis_logs table exists and create/update it as needed
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
    print("🚀 Checking and setting up ai_analysis_logs table")
    print("=" * 50)
    
    try:
        sql_executor = SupabaseSQL()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Please set the following environment variables:")
        print("  - SUPABASE_PROJECT_ID")
        print("  - SUPABASE_ACCESS_TOKEN")
        return
    
    # Step 1: Check if table exists
    print("\n📊 Checking if ai_analysis_logs table exists...")
    check_table_sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'ai_analysis_logs'
    );
    """
    
    result = sql_executor.execute_sql(check_table_sql)
    
    table_exists = False
    if result and 'data' in result:
        table_exists = result['data'][0]['exists'] if result['data'] else False
    
    if not table_exists:
        print("⚠️  Table does not exist. Creating it now...")
        
        # Read the table creation SQL
        sql_file = Path(__file__).parent.parent / 'database' / 'ai_analysis_logs_fixed.sql'
        
        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return
        
        with open(sql_file, 'r') as f:
            create_table_sql = f.read()
        
        # First, we need to ensure the referenced tables exist
        print("\n🔨 Checking dependencies...")
        
        # Check if analysis_configs exists
        check_deps_sql = """
        SELECT 
            EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'analysis_configs') as configs_exists,
            EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'analysis_tasks') as tasks_exists;
        """
        
        deps_result = sql_executor.execute_sql(check_deps_sql)
        
        if deps_result and 'data' in deps_result and deps_result['data']:
            configs_exists = deps_result['data'][0]['configs_exists']
            tasks_exists = deps_result['data'][0]['tasks_exists']
            
            if not configs_exists or not tasks_exists:
                print("⚠️  Dependencies missing. Creating base tables first...")
                
                # Read and execute schema.sql which should have all tables
                schema_file = Path(__file__).parent.parent / 'database' / 'schema.sql'
                if schema_file.exists():
                    with open(schema_file, 'r') as f:
                        schema_sql = f.read()
                    
                    print("🔨 Creating all tables from schema.sql...")
                    result = sql_executor.execute_sql(schema_sql)
                    
                    if not result:
                        print("❌ Failed to create base tables")
                        return
                else:
                    print("❌ schema.sql not found")
                    return
        
        # Now create the ai_analysis_logs table
        print("\n🔨 Creating ai_analysis_logs table...")
        result = sql_executor.execute_sql(create_table_sql)
        
        if result:
            print("✅ Table created successfully!")
        else:
            print("❌ Failed to create table")
            return
    else:
        print("✅ Table already exists!")
    
    # Step 2: Check if token columns exist
    print("\n📊 Checking for token columns...")
    check_columns_sql = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public' 
    AND table_name = 'ai_analysis_logs'
    AND column_name IN ('input_tokens', 'output_tokens', 'tokens_used', 'estimated_cost')
    ORDER BY column_name;
    """
    
    result = sql_executor.execute_sql(check_columns_sql)
    
    if result and 'data' in result:
        existing_columns = {row['column_name']: row for row in result.get('data', [])}
        
        print("\nExisting columns:")
        for col_name, col_info in existing_columns.items():
            print(f"  ✓ {col_name}: {col_info['data_type']}")
        
        # Check if we need to add any columns
        required_columns = ['input_tokens', 'output_tokens', 'tokens_used', 'estimated_cost']
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"\n⚠️  Missing columns: {', '.join(missing_columns)}")
            
            # Add missing columns
            for col in missing_columns:
                if col in ['input_tokens', 'output_tokens', 'tokens_used']:
                    col_type = 'INTEGER'
                elif col == 'estimated_cost':
                    col_type = 'DECIMAL(10, 6)'
                
                add_col_sql = f"ALTER TABLE ai_analysis_logs ADD COLUMN IF NOT EXISTS {col} {col_type};"
                print(f"\n🔨 Adding column: {col}")
                result = sql_executor.execute_sql(add_col_sql)
                
                if result:
                    print(f"  ✓ Added {col}")
                else:
                    print(f"  ✗ Failed to add {col}")
        else:
            print("\n✅ All required columns exist!")
    
    # Step 3: Check and update the view
    print("\n📊 Updating daily_ai_costs view...")
    update_view_sql = """
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
    """
    
    result = sql_executor.execute_sql(update_view_sql)
    
    if result:
        print("✅ View updated successfully!")
    else:
        print("❌ Failed to update view")
    
    # Step 4: Final verification
    print("\n✅ Final verification...")
    verify_sql = """
    SELECT 
        c.column_name,
        c.data_type,
        c.is_nullable
    FROM information_schema.columns c
    WHERE c.table_schema = 'public' 
    AND c.table_name = 'ai_analysis_logs'
    AND c.column_name IN ('input_tokens', 'output_tokens', 'tokens_used', 'estimated_cost')
    ORDER BY c.ordinal_position;
    """
    
    result = sql_executor.execute_sql(verify_sql)
    
    if result and 'data' in result:
        print("\nFinal column status:")
        for col in result['data']:
            print(f"  ✓ {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    
    print("\n✨ Setup complete!")
    print("\nThe ai_analysis_logs table now has:")
    print("  ✓ input_tokens column for tracking input token usage")
    print("  ✓ output_tokens column for tracking output token usage")
    print("  ✓ tokens_used column for total token usage")
    print("  ✓ estimated_cost column for cost tracking")
    print("  ✓ daily_ai_costs view with token breakdowns")

if __name__ == "__main__":
    main()