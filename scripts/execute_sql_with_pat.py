#!/usr/bin/env python3
"""
Execute SQL using Supabase Personal Access Token
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class SupabaseSQL:
    def __init__(self):
        self.project_id = os.getenv('SUPABASE_PROJECT_ID')
        self.access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
        
        if not self.project_id or not self.access_token:
            raise ValueError("Missing SUPABASE_PROJECT_ID or SUPABASE_ACCESS_TOKEN")
        
        self.api_base = "https://api.supabase.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def execute_sql(self, sql: str):
        """Execute SQL query using Management API"""
        endpoint = f"{self.api_base}/projects/{self.project_id}/database/query"
        
        response = requests.post(
            endpoint,
            headers=self.headers,
            json={"query": sql}
        )
        
        if response.status_code in [200, 201]:
            try:
                return {"data": response.json(), "status": response.status_code}
            except:
                return {"data": response.text, "status": response.status_code}
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None

def main():
    print("🚀 Executing SQL with Personal Access Token")
    print("=" * 50)
    
    sql_executor = SupabaseSQL()
    
    # First, let's test with a simple query
    print("\n📊 Testing connection with simple query...")
    result = sql_executor.execute_sql("SELECT current_database(), version();")
    
    if result:
        print("✅ Connection successful!")
        print(f"Database: {json.dumps(result, indent=2)}")
    else:
        print("❌ Connection failed")
        return
    
    # Now let's create the analysis tables
    print("\n🔨 Creating analysis tables...")
    
    # Read schema file
    schema_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'database',
        'schema.sql'
    )
    
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    
    # Execute the schema
    result = sql_executor.execute_sql(schema_sql)
    
    if result:
        print("✅ Schema executed successfully!")
    else:
        print("❌ Failed to execute schema")
        return
    
    # Verify tables were created
    print("\n📋 Verifying tables...")
    check_sql = """
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename LIKE 'analysis_%'
    ORDER BY tablename;
    """
    
    result = sql_executor.execute_sql(check_sql)
    if result and 'data' in result:
        print("Created tables:")
        for row in result['data']:
            print(f"  ✓ {row['tablename']}")
    
    print("\n✅ Database setup complete!")

if __name__ == "__main__":
    main()