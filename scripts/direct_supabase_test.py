#!/usr/bin/env python3
"""
Direct Supabase operations test
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()

def main():
    # Create client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return
    
    client = create_client(url, key)
    print("✅ Connected to Supabase")
    
    # Check what tables exist
    print("\n📊 Checking existing tables...")
    
    tables_to_check = [
        'spypoint_images',
        'spypoint_telemetry',
        'analysis_configs',
        'image_analysis_results',
        'analysis_tasks',
        'analysis_alerts',
        'analysis_cache',
        'analysis_costs'
    ]
    
    existing_tables = []
    missing_tables = []
    
    for table in tables_to_check:
        try:
            result = client.table(table).select('count').execute()
            count = result.data[0]['count'] if result.data else 0
            existing_tables.append(f"  ✓ {table}: {count} rows")
        except Exception as e:
            if "does not exist" in str(e):
                missing_tables.append(f"  ✗ {table}: does not exist")
            else:
                missing_tables.append(f"  ✗ {table}: {str(e)}")
    
    print("\nExisting tables:")
    for table in existing_tables:
        print(table)
    
    if missing_tables:
        print("\nMissing tables:")
        for table in missing_tables:
            print(table)
    
    # Show storage buckets
    print("\n📦 Storage buckets:")
    try:
        buckets = client.storage.list_buckets()
        for bucket in buckets:
            print(f"  - {bucket['name']} ({'Public' if bucket.get('public') else 'Private'})")
    except Exception as e:
        print(f"  Error listing buckets: {e}")
    
    # Show sample data from spypoint_images
    print("\n🖼️  Recent images:")
    try:
        images = client.table('spypoint_images').select('image_id, camera_name, downloaded_at').order('downloaded_at', desc=True).limit(5).execute()
        for img in images.data:
            print(f"  - {img['camera_name']}: {img['image_id']} ({img['downloaded_at']})")
    except Exception as e:
        print(f"  Error fetching images: {e}")
    
    print("\n✅ Connection test complete!")
    
    if missing_tables and 'analysis_configs' in str(missing_tables):
        print("\n⚠️  Analysis tables are missing!")
        print("Run: python scripts/create_tables.py")
        print("Then execute the SQL in Supabase Dashboard")

if __name__ == "__main__":
    main()