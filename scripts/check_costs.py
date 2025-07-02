#!/usr/bin/env python3
"""
Debug script to check cost tracking in the database
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.supabase_client import SupabaseClient

load_dotenv()

def check_costs():
    """Check what costs are in the database"""
    
    # Initialize Supabase client
    supabase = SupabaseClient(
        url=os.getenv('SUPABASE_URL'),
        key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    )
    
    # Get recent AI analysis logs
    try:
        # Get all logs from today
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        
        response = supabase.client.table('ai_analysis_logs').select(
            'id, created_at, model_name, tokens_used, input_tokens, output_tokens, estimated_cost'
        ).gte('created_at', today.isoformat()).lt('created_at', tomorrow.isoformat()).execute()
        
        print(f"\nFound {len(response.data)} analysis logs from today")
        print("-" * 80)
        
        total_cost = 0
        for log in response.data:
            print(f"ID: {log['id'][:8]}...")
            print(f"  Created: {log['created_at']}")
            print(f"  Model: {log['model_name']}")
            print(f"  Tokens Used: {log.get('tokens_used', 'None')}")
            print(f"  Input Tokens: {log.get('input_tokens', 'None')}")
            print(f"  Output Tokens: {log.get('output_tokens', 'None')}")
            print(f"  Estimated Cost: ${log.get('estimated_cost', 0) or 0:.6f}")
            print()
            
            cost = log.get('estimated_cost', 0) or 0
            total_cost += cost
        
        print(f"Total cost today: ${total_cost:.6f}")
        
        # Check all-time costs
        all_response = supabase.client.table('ai_analysis_logs').select(
            'estimated_cost'
        ).execute()
        
        all_time_cost = sum(log.get('estimated_cost', 0) or 0 for log in all_response.data)
        print(f"Total all-time cost: ${all_time_cost:.6f}")
        
    except Exception as e:
        print(f"Error checking costs: {e}")

if __name__ == "__main__":
    print("Checking cost tracking in database...")
    check_costs()