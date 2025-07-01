#!/usr/bin/env python3
"""
Test Supabase connection and show available operations
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def test_connection():
    """Test Supabase connection and display available operations"""
    
    print("🔍 Testing Supabase Connection")
    print("=" * 50)
    
    # Show configured values
    print("\n📋 Configuration:")
    print(f"  URL: {os.getenv('SUPABASE_URL')}")
    print(f"  Project ID: {os.getenv('SUPABASE_PROJECT_ID')}")
    print(f"  Access Token: {'✓ Configured' if os.getenv('SUPABASE_ACCESS_TOKEN') else '✗ Missing'}")
    print(f"  Service Role Key: {'✓ Configured' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '✗ Missing'}")
    
    # Test client connection
    print("\n🔌 Testing Client Connection...")
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not key:
            print("  ✗ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
            return
            
        client = create_client(url, key)
        print("  ✓ Client created successfully")
        
        # Test a simple query
        print("\n📊 Testing Database Access...")
        
        # Try to count rows in analysis_configs
        result = client.table('analysis_configs').select('count').execute()
        if result.data:
            print(f"  ✓ analysis_configs table accessible ({result.data[0]['count']} rows)")
        else:
            print("  ⚠️  analysis_configs table exists but is empty")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return
    
    # Show available operations
    print("\n🛠️  Available Operations:")
    print("\n  With current setup, you can:")
    print("  ✓ Query and modify all tables")
    print("  ✓ Upload/download files from storage")
    print("  ✓ Execute RPC functions")
    print("  ✓ Manage real-time subscriptions")
    
    print("\n  With the admin scripts:")
    print("  ✓ Create/modify tables (supabase_admin.py)")
    print("  ✓ Manage storage buckets")
    print("  ✓ Run migrations")
    print("  ✓ Monitor API usage")
    print("  ✓ Setup webhooks and functions (supabase_management.py)")
    
    # Show sample commands
    print("\n📝 Sample Commands:")
    print("\n  # List all tables")
    print("  python scripts/supabase_admin.py list-tables")
    print("\n  # Get project overview")
    print("  python scripts/supabase_management.py overview")
    print("\n  # Create sample data")
    print("  python scripts/supabase_admin.py create-sample")
    print("\n  # Setup all analysis tables")
    print("  python scripts/supabase_management.py setup-tables")
    
    print("\n✅ Connection test complete!")

if __name__ == "__main__":
    test_connection()