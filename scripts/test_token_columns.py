#!/usr/bin/env python3
"""
Test that the token columns are working correctly in ai_analysis_logs table
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.db.supabase_client import SupabaseClient

load_dotenv()

def main():
    print("🧪 Testing token columns in ai_analysis_logs table")
    print("=" * 50)
    
    # Get credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Missing SUPABASE_URL or SUPABASE_ANON_KEY")
        return
    
    # Create Supabase client
    client = SupabaseClient(supabase_url, supabase_key)
    
    # Test data with token values
    test_image_id = f"test-image-{uuid.uuid4().hex[:8]}"
    test_session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    
    print(f"\n📝 Creating test record with:")
    print(f"  - Image ID: {test_image_id}")
    print(f"  - Session ID: {test_session_id}")
    print(f"  - Input tokens: 150")
    print(f"  - Output tokens: 75")
    print(f"  - Total tokens: 225")
    
    # Use the save_ai_analysis_log method which includes token parameters
    log_id = None
    try:
        import asyncio
        
        async def save_test_log():
            return await client.save_ai_analysis_log(
                image_id=test_image_id,
                image_url="https://example.com/test-image.jpg",
                camera_name="Test Camera",
                captured_at=datetime.utcnow().isoformat(),
                analysis_type="wildlife_detection",
                prompt_text="Test prompt for token column verification",
                custom_prompt=False,
                model_provider="openai",
                model_name="gpt-4o-mini",
                raw_response='{"test": "response", "animals": ["deer"]}',
                parsed_response={"test": "response", "animals": ["deer"]},
                confidence=0.95,
                analysis_successful=True,
                error_message=None,
                processing_time_ms=1250,
                tokens_used=225,
                input_tokens=150,
                output_tokens=75,
                estimated_cost=0.000084,  # Based on gpt-4o-mini pricing
                session_id=test_session_id,
                user_initiated=True,
                notes="Test record for token column verification"
            )
        
        log_id = asyncio.run(save_test_log())
        
        if log_id:
            print(f"\n✅ Successfully created test record with ID: {log_id}")
        else:
            print("\n❌ Failed to create test record")
            return
            
    except Exception as e:
        print(f"\n❌ Error creating test record: {e}")
        return
    
    # Verify the record was saved with token values
    print("\n🔍 Verifying saved record...")
    
    try:
        # Query the record directly
        result = client.client.table('ai_analysis_logs').select(
            'id,image_id,model_provider,model_name,tokens_used,input_tokens,output_tokens,estimated_cost'
        ).eq('id', log_id).single().execute()
        
        if result.data:
            record = result.data
            print("\n📊 Retrieved record:")
            print(f"  - ID: {record['id']}")
            print(f"  - Image ID: {record['image_id']}")
            print(f"  - Model: {record['model_provider']}/{record['model_name']}")
            print(f"  - Total tokens: {record['tokens_used']}")
            print(f"  - Input tokens: {record['input_tokens']}")
            print(f"  - Output tokens: {record['output_tokens']}")
            print(f"  - Estimated cost: ${record['estimated_cost']}")
            
            # Verify token values
            if (record['input_tokens'] == 150 and 
                record['output_tokens'] == 75 and 
                record['tokens_used'] == 225):
                print("\n✅ Token values correctly stored!")
            else:
                print("\n❌ Token values don't match expected values")
        else:
            print("\n❌ Could not retrieve record")
            
    except Exception as e:
        print(f"\n❌ Error retrieving record: {e}")
    
    # Test the daily_ai_costs view
    print("\n📊 Testing daily_ai_costs view...")
    
    try:
        # Query the view
        result = client.client.rpc('get_daily_costs', {}).execute()
        # Since we can't directly query views with Supabase Python client, 
        # let's use a raw SQL query approach
        
        # Actually, let's query our session to see aggregated data
        result = client.client.table('ai_analysis_logs').select(
            'model_provider,model_name,tokens_used,input_tokens,output_tokens,estimated_cost'
        ).eq('session_id', test_session_id).execute()
        
        if result.data:
            print(f"\n✅ Found {len(result.data)} record(s) for test session")
            
            # Calculate totals
            total_input = sum(r['input_tokens'] or 0 for r in result.data)
            total_output = sum(r['output_tokens'] or 0 for r in result.data)
            total_tokens = sum(r['tokens_used'] or 0 for r in result.data)
            total_cost = sum(r['estimated_cost'] or 0 for r in result.data)
            
            print(f"\nSession totals:")
            print(f"  - Total input tokens: {total_input}")
            print(f"  - Total output tokens: {total_output}")
            print(f"  - Total tokens: {total_tokens}")
            print(f"  - Total cost: ${total_cost:.6f}")
            
    except Exception as e:
        print(f"\n❌ Error testing view: {e}")
    
    # Cleanup
    if log_id:
        print("\n🧹 Cleaning up test record...")
        try:
            client.client.table('ai_analysis_logs').delete().eq('id', log_id).execute()
            print("✅ Test record deleted")
        except Exception as e:
            print(f"❌ Error deleting test record: {e}")
    
    print("\n✨ Token column testing complete!")

if __name__ == "__main__":
    main()