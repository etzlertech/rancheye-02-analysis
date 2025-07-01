#!/usr/bin/env python3
"""
Supabase Administration Script
Manages tables, storage, migrations, and other admin tasks
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client

load_dotenv()

def get_supabase_client():
    """Create and return Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    
    return create_client(url, key)

class SupabaseAdmin:
    def __init__(self):
        self.project_id = os.getenv('SUPABASE_PROJECT_ID')
        self.access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.url = os.getenv('SUPABASE_URL')
        
        if not all([self.project_id, self.access_token, self.service_role_key]):
            raise ValueError("Missing required Supabase credentials")
        
        self.api_base = f"https://api.supabase.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Get client for data operations
        self.client = get_supabase_client()
    
    def list_tables(self):
        """List all tables in the database"""
        print("\n📊 Listing all tables...")
        
        # Use SQL query to get table information
        query = """
        SELECT 
            schemaname,
            tablename,
            tableowner
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename;
        """
        
        result = self.client.rpc('exec_sql', {'query': query}).execute()
        
        if result.data:
            print(f"\nFound {len(result.data)} tables:")
            for table in result.data:
                print(f"  - {table['schemaname']}.{table['tablename']} (owner: {table['tableowner']})")
        else:
            print("No tables found or exec_sql function not available")
            
            # Fallback: Try to query known tables
            print("\nTrying to query known tables directly...")
            tables = [
                'spypoint_images',
                'spypoint_telemetry', 
                'analysis_configs',
                'image_analysis_results',
                'analysis_tasks',
                'analysis_alerts',
                'analysis_cache',
                'analysis_costs'
            ]
            
            for table in tables:
                try:
                    result = self.client.table(table).select('count').execute()
                    count = result.data[0]['count'] if result.data else 0
                    print(f"  ✓ {table}: {count} rows")
                except Exception as e:
                    print(f"  ✗ {table}: {str(e)}")
    
    def create_rpc_function(self):
        """Create an RPC function for executing SQL (if it doesn't exist)"""
        print("\n🔧 Creating exec_sql RPC function...")
        
        create_function_sql = """
        CREATE OR REPLACE FUNCTION exec_sql(query text)
        RETURNS json
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            result json;
        BEGIN
            EXECUTE format('SELECT json_agg(row_to_json(t)) FROM (%s) t', query) INTO result;
            RETURN COALESCE(result, '[]'::json);
        END;
        $$;
        """
        
        # Note: This would need to be executed via Supabase SQL editor
        print("To enable SQL execution, run this in Supabase SQL editor:")
        print(create_function_sql)
    
    def list_storage_buckets(self):
        """List all storage buckets"""
        print("\n📦 Listing storage buckets...")
        
        buckets = self.client.storage.list_buckets()
        
        if buckets:
            print(f"\nFound {len(buckets)} buckets:")
            for bucket in buckets:
                public = "Public" if bucket.get('public') else "Private"
                print(f"  - {bucket['name']} ({public})")
                print(f"    Created: {bucket.get('created_at', 'Unknown')}")
                print(f"    Size limit: {bucket.get('file_size_limit', 'No limit')}")
        else:
            print("No buckets found")
    
    def create_storage_bucket(self, name, public=False):
        """Create a new storage bucket"""
        print(f"\n📦 Creating bucket '{name}'...")
        
        try:
            self.client.storage.create_bucket(
                name,
                {
                    'public': public,
                    'file_size_limit': 10485760,  # 10MB
                    'allowed_mime_types': ['image/jpeg', 'image/png', 'image/webp']
                }
            )
            print(f"✓ Bucket '{name}' created successfully!")
        except Exception as e:
            print(f"✗ Error creating bucket: {e}")
    
    def get_database_size(self):
        """Get database size information"""
        print("\n💾 Database size information...")
        
        # Use Management API
        endpoint = f"{self.api_base}/projects/{self.project_id}/database"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print(f"  Database size: {data.get('size', 'Unknown')}")
                print(f"  Status: {data.get('status', 'Unknown')}")
            else:
                print(f"  Unable to fetch database info: {response.status_code}")
        except Exception as e:
            print(f"  Error: {e}")
    
    def run_migration(self, migration_file):
        """Run a SQL migration file"""
        print(f"\n🔄 Running migration: {migration_file}")
        
        if not os.path.exists(migration_file):
            print(f"✗ Migration file not found: {migration_file}")
            return
        
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print("Migration content:")
        print("-" * 50)
        print(sql[:500] + "..." if len(sql) > 500 else sql)
        print("-" * 50)
        
        # Note: Actual execution would require direct database access
        print("\nTo run this migration:")
        print("1. Go to Supabase Dashboard > SQL Editor")
        print("2. Paste the migration content")
        print("3. Click 'Run'")
    
    def create_sample_data(self):
        """Create sample data for testing"""
        print("\n🧪 Creating sample data...")
        
        # Create sample analysis config
        try:
            config = {
                'name': 'Wildlife Detection Test',
                'analysis_type': 'animal_detection',
                'model_provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'prompt_template': 'Analyze this trail camera image for any animals. Identify the species if possible, count how many, and note if they are livestock or wildlife. Respond with JSON: {"animals_detected": boolean, "animals": [{"species": "name or unknown", "count": number, "type": "livestock|wildlife|unknown", "confidence": float}], "reasoning": "explanation"}',
                'threshold': 0.8,
                'active': True
            }
            
            result = self.client.table('analysis_configs').insert(config).execute()
            print("✓ Created sample analysis config")
            
        except Exception as e:
            print(f"✗ Error creating sample config: {e}")
        
        # Create sample task
        try:
            task = {
                'image_id': 'sample-image-001',
                'config_id': result.data[0]['id'] if result.data else None,
                'status': 'pending',
                'priority': 5
            }
            
            self.client.table('analysis_tasks').insert(task).execute()
            print("✓ Created sample analysis task")
            
        except Exception as e:
            print(f"✗ Error creating sample task: {e}")
    
    def get_table_info(self, table_name):
        """Get detailed information about a specific table"""
        print(f"\n🔍 Table info for '{table_name}':")
        
        try:
            # Get row count
            result = self.client.table(table_name).select('count').execute()
            count = result.data[0]['count'] if result.data else 0
            print(f"  Row count: {count}")
            
            # Get sample data
            sample = self.client.table(table_name).select('*').limit(1).execute()
            if sample.data:
                print(f"  Columns: {', '.join(sample.data[0].keys())}")
                print("\n  Sample row:")
                for key, value in sample.data[0].items():
                    print(f"    {key}: {value}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    def monitor_api_usage(self):
        """Check API usage and limits"""
        print("\n📈 API Usage Information...")
        
        endpoint = f"{self.api_base}/projects/{self.project_id}/usage"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print(f"  Database requests: {data.get('database_requests', 'Unknown')}")
                print(f"  Storage usage: {data.get('storage_bytes', 'Unknown')} bytes")
                print(f"  Auth users: {data.get('auth_users', 'Unknown')}")
            else:
                print(f"  Unable to fetch usage info: {response.status_code}")
        except Exception as e:
            print(f"  Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Supabase Administration Tool')
    parser.add_argument('command', choices=[
        'list-tables',
        'list-buckets',
        'create-bucket',
        'db-size',
        'run-migration',
        'create-sample',
        'table-info',
        'api-usage',
        'create-rpc'
    ], help='Command to execute')
    parser.add_argument('--name', help='Name parameter (for create-bucket, table-info)')
    parser.add_argument('--public', action='store_true', help='Make bucket public')
    parser.add_argument('--file', help='Migration file path')
    
    args = parser.parse_args()
    
    admin = SupabaseAdmin()
    
    if args.command == 'list-tables':
        admin.list_tables()
    elif args.command == 'list-buckets':
        admin.list_storage_buckets()
    elif args.command == 'create-bucket':
        if not args.name:
            print("Error: --name required for create-bucket")
            return
        admin.create_storage_bucket(args.name, args.public)
    elif args.command == 'db-size':
        admin.get_database_size()
    elif args.command == 'run-migration':
        if not args.file:
            print("Error: --file required for run-migration")
            return
        admin.run_migration(args.file)
    elif args.command == 'create-sample':
        admin.create_sample_data()
    elif args.command == 'table-info':
        if not args.name:
            print("Error: --name required for table-info")
            return
        admin.get_table_info(args.name)
    elif args.command == 'api-usage':
        admin.monitor_api_usage()
    elif args.command == 'create-rpc':
        admin.create_rpc_function()

if __name__ == "__main__":
    main()