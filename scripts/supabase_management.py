#!/usr/bin/env python3
"""
Advanced Supabase Management Script
Uses Supabase Management API for project administration
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
import argparse
from typing import Dict, List, Optional

load_dotenv()

class SupabaseManagementAPI:
    """Interface to Supabase Management API"""
    
    def __init__(self):
        self.project_id = os.getenv('SUPABASE_PROJECT_ID')
        self.access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
        
        if not all([self.project_id, self.access_token]):
            raise ValueError("SUPABASE_PROJECT_ID and SUPABASE_ACCESS_TOKEN required")
        
        self.api_base = "https://api.supabase.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request"""
        url = f"{self.api_base}{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            json=data
        )
        
        if response.status_code >= 400:
            print(f"Error {response.status_code}: {response.text}")
            return None
        
        return response.json() if response.text else {}
    
    def get_project_info(self) -> Dict:
        """Get project information"""
        return self._request("GET", f"/projects/{self.project_id}")
    
    def get_database_info(self) -> Dict:
        """Get database configuration"""
        return self._request("GET", f"/projects/{self.project_id}/database")
    
    def run_sql_query(self, query: str) -> Dict:
        """Execute SQL query via API"""
        return self._request("POST", f"/projects/{self.project_id}/database/query", {
            "query": query
        })
    
    def create_database_function(self, name: str, definition: str) -> Dict:
        """Create a database function"""
        return self._request("POST", f"/projects/{self.project_id}/database/functions", {
            "name": name,
            "definition": definition
        })
    
    def list_database_functions(self) -> List[Dict]:
        """List all database functions"""
        return self._request("GET", f"/projects/{self.project_id}/database/functions")
    
    def update_auth_settings(self, settings: Dict) -> Dict:
        """Update authentication settings"""
        return self._request("PATCH", f"/projects/{self.project_id}/config/auth", settings)
    
    def get_api_keys(self) -> Dict:
        """Get project API keys"""
        return self._request("GET", f"/projects/{self.project_id}/api-keys")
    
    def create_database_webhook(self, table: str, events: List[str], url: str) -> Dict:
        """Create a database webhook"""
        return self._request("POST", f"/projects/{self.project_id}/database/webhooks", {
            "table": table,
            "events": events,
            "url": url,
            "enabled": True
        })
    
    def get_database_backups(self) -> List[Dict]:
        """List database backups"""
        return self._request("GET", f"/projects/{self.project_id}/database/backups")
    
    def trigger_database_backup(self) -> Dict:
        """Trigger a manual database backup"""
        return self._request("POST", f"/projects/{self.project_id}/database/backups")
    
    def get_database_extensions(self) -> List[Dict]:
        """List installed database extensions"""
        return self._request("GET", f"/projects/{self.project_id}/database/extensions")
    
    def enable_database_extension(self, extension: str) -> Dict:
        """Enable a database extension"""
        return self._request("POST", f"/projects/{self.project_id}/database/extensions", {
            "name": extension
        })
    
    def get_storage_policies(self, bucket: str) -> List[Dict]:
        """Get storage bucket policies"""
        return self._request("GET", f"/projects/{self.project_id}/storage/buckets/{bucket}/policies")
    
    def create_storage_policy(self, bucket: str, name: str, definition: str) -> Dict:
        """Create a storage policy"""
        return self._request("POST", f"/projects/{self.project_id}/storage/buckets/{bucket}/policies", {
            "name": name,
            "definition": definition
        })
    
    def get_edge_functions(self) -> List[Dict]:
        """List edge functions"""
        return self._request("GET", f"/projects/{self.project_id}/functions")
    
    def deploy_edge_function(self, name: str, code: str) -> Dict:
        """Deploy an edge function"""
        return self._request("POST", f"/projects/{self.project_id}/functions", {
            "name": name,
            "verify_jwt": True,
            "body": code
        })

class SupabaseProjectManager:
    """High-level project management operations"""
    
    def __init__(self):
        self.api = SupabaseManagementAPI()
    
    def show_project_overview(self):
        """Display project overview"""
        print("\n🏗️  PROJECT OVERVIEW")
        print("=" * 50)
        
        # Get project info
        project = self.api.get_project_info()
        if project:
            print(f"Name: {project.get('name', 'Unknown')}")
            print(f"Region: {project.get('region', 'Unknown')}")
            print(f"Status: {project.get('status', 'Unknown')}")
            print(f"Created: {project.get('created_at', 'Unknown')}")
            print(f"Organization: {project.get('organization_id', 'Unknown')}")
        
        # Get database info
        print("\n📊 DATABASE")
        print("-" * 30)
        db = self.api.get_database_info()
        if db:
            print(f"Version: PostgreSQL {db.get('version', 'Unknown')}")
            print(f"Size: {db.get('size', 'Unknown')}")
            print(f"Status: {db.get('status', 'Unknown')}")
    
    def setup_analysis_tables(self):
        """Create all required analysis tables"""
        print("\n🔨 Setting up analysis tables...")
        
        # Read schema file
        schema_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'database',
            'schema.sql'
        )
        
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema
            result = self.api.run_sql_query(schema_sql)
            if result:
                print("✓ Schema executed successfully")
            else:
                print("✗ Failed to execute schema")
        else:
            print("✗ Schema file not found")
    
    def enable_useful_extensions(self):
        """Enable useful PostgreSQL extensions"""
        print("\n🔧 Enabling PostgreSQL extensions...")
        
        extensions = [
            ('uuid-ossp', 'UUID generation'),
            ('pgcrypto', 'Cryptographic functions'),
            ('pg_stat_statements', 'Query performance monitoring'),
            ('plv8', 'JavaScript in PostgreSQL')
        ]
        
        for ext, desc in extensions:
            print(f"\n  Enabling {ext} ({desc})...")
            result = self.api.enable_database_extension(ext)
            if result:
                print(f"  ✓ {ext} enabled")
            else:
                print(f"  ✗ Failed to enable {ext}")
    
    def setup_storage_buckets(self):
        """Setup storage buckets with policies"""
        print("\n📦 Setting up storage buckets...")
        
        # Note: Creating buckets via API requires different endpoint
        # This is a placeholder for the logic
        buckets = [
            {
                'name': 'analysis-results',
                'public': False,
                'policies': [
                    {
                        'name': 'Service role access',
                        'definition': 'bucket_id = "analysis-results"'
                    }
                ]
            }
        ]
        
        for bucket in buckets:
            print(f"\nBucket: {bucket['name']}")
            # Would create bucket and policies here
    
    def create_helper_functions(self):
        """Create useful database functions"""
        print("\n🎯 Creating helper functions...")
        
        functions = [
            {
                'name': 'get_pending_analysis_tasks',
                'definition': '''
                CREATE OR REPLACE FUNCTION get_pending_analysis_tasks(limit_count INT DEFAULT 10)
                RETURNS TABLE(
                    task_id UUID,
                    image_id TEXT,
                    config_id UUID,
                    priority INT,
                    created_at TIMESTAMPTZ
                )
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        id as task_id,
                        image_id,
                        config_id,
                        priority,
                        created_at
                    FROM analysis_tasks
                    WHERE status = 'pending'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT limit_count;
                END;
                $$;
                '''
            },
            {
                'name': 'update_task_status',
                'definition': '''
                CREATE OR REPLACE FUNCTION update_task_status(
                    task_id UUID,
                    new_status TEXT,
                    result_data JSONB DEFAULT NULL
                )
                RETURNS BOOLEAN
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    UPDATE analysis_tasks
                    SET 
                        status = new_status,
                        completed_at = CASE 
                            WHEN new_status IN ('completed', 'failed') 
                            THEN NOW() 
                            ELSE NULL 
                        END,
                        result = COALESCE(result_data, result)
                    WHERE id = task_id;
                    
                    RETURN FOUND;
                END;
                $$;
                '''
            }
        ]
        
        for func in functions:
            print(f"\n  Creating function: {func['name']}")
            result = self.api.create_database_function(
                func['name'],
                func['definition']
            )
            if result:
                print(f"  ✓ {func['name']} created")
            else:
                print(f"  ✗ Failed to create {func['name']}")
    
    def setup_webhooks(self):
        """Setup database webhooks for real-time events"""
        print("\n🪝 Setting up webhooks...")
        
        webhooks = [
            {
                'table': 'analysis_alerts',
                'events': ['INSERT'],
                'url': os.getenv('ALERT_WEBHOOK_URL', '')
            }
        ]
        
        for webhook in webhooks:
            if webhook['url']:
                print(f"\n  Creating webhook for {webhook['table']}")
                result = self.api.create_database_webhook(
                    webhook['table'],
                    webhook['events'],
                    webhook['url']
                )
                if result:
                    print(f"  ✓ Webhook created")
                else:
                    print(f"  ✗ Failed to create webhook")
            else:
                print(f"\n  ⚠️  No webhook URL configured for {webhook['table']}")
    
    def show_api_keys(self):
        """Display API keys"""
        print("\n🔑 API KEYS")
        print("=" * 50)
        
        keys = self.api.get_api_keys()
        if keys:
            for key_type, key_value in keys.items():
                if key_value:
                    masked = key_value[:20] + "..." + key_value[-10:]
                    print(f"{key_type}: {masked}")

def main():
    parser = argparse.ArgumentParser(description='Advanced Supabase Management')
    parser.add_argument('command', choices=[
        'overview',
        'setup-tables',
        'enable-extensions',
        'setup-storage',
        'create-functions',
        'setup-webhooks',
        'show-keys',
        'full-setup'
    ], help='Management command')
    
    args = parser.parse_args()
    
    manager = SupabaseProjectManager()
    
    if args.command == 'overview':
        manager.show_project_overview()
    elif args.command == 'setup-tables':
        manager.setup_analysis_tables()
    elif args.command == 'enable-extensions':
        manager.enable_useful_extensions()
    elif args.command == 'setup-storage':
        manager.setup_storage_buckets()
    elif args.command == 'create-functions':
        manager.create_helper_functions()
    elif args.command == 'setup-webhooks':
        manager.setup_webhooks()
    elif args.command == 'show-keys':
        manager.show_api_keys()
    elif args.command == 'full-setup':
        print("🚀 Running full setup...")
        manager.show_project_overview()
        manager.enable_useful_extensions()
        manager.setup_analysis_tables()
        manager.create_helper_functions()
        manager.setup_webhooks()
        print("\n✅ Full setup complete!")

if __name__ == "__main__":
    main()