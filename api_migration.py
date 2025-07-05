#!/usr/bin/env python3
"""
Test if migration columns exist and create test endpoint
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.supabase_client import SupabaseClient

load_dotenv()

def test_migration():
    """Test if the new columns exist by attempting to use them"""
    
    # Initialize Supabase client
    supabase = SupabaseClient(
        url=os.getenv('SUPABASE_URL'),
        key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    )
    
    print("Testing if migration columns exist...")
    
    try:
        # Try to select the new columns
        print("\n1. Testing quality_rating column...")
        response = supabase.client.table('ai_analysis_logs').select(
            'id, quality_rating, user_notes, notes_updated_at'
        ).limit(1).execute()
        
        print("✓ New columns appear to exist!")
        print(f"Sample data: {response.data}")
        
        # Try to update a record with new columns (if any exist)
        if response.data and len(response.data) > 0:
            test_id = response.data[0]['id']
            print(f"\n2. Testing update on record ID {test_id}...")
            
            update_response = supabase.client.table('ai_analysis_logs').update({
                'quality_rating': 4,
                'user_notes': 'Test note from migration script',
                'notes_updated_at': datetime.utcnow().isoformat()
            }).eq('id', test_id).execute()
            
            print("✓ Update successful!")
            print(f"Updated data: {update_response.data}")
            
            # Clean up test data
            print("\n3. Cleaning up test data...")
            cleanup_response = supabase.client.table('ai_analysis_logs').update({
                'quality_rating': None,
                'user_notes': None,
                'notes_updated_at': None
            }).eq('id', test_id).execute()
            
            print("✓ Cleanup successful!")
        
        print("\n✅ Migration appears to be complete! The new columns are working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nThe migration columns don't exist yet.")
        print("Please run the SQL migration in your Supabase dashboard.")
        return False

if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)