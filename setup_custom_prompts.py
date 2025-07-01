#!/usr/bin/env python3
"""
Simple script to set up the custom_prompt_templates table in Supabase.
Run this to enable the custom prompt template feature.
"""

import os
import requests
from dotenv import load_dotenv

def setup_custom_prompt_templates():
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return False
    
    print(f"🔗 Connecting to: {supabase_url}")
    
    # Simple SQL to create the table
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS custom_prompt_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            description TEXT,
            prompt_text TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            is_system BOOLEAN DEFAULT FALSE,
            created_by TEXT DEFAULT 'web_user',
            usage_count INTEGER DEFAULT 0,
            last_used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_custom_prompts_analysis_type 
        ON custom_prompt_templates(analysis_type);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_custom_prompts_is_default 
        ON custom_prompt_templates(is_default) WHERE is_default = TRUE;
        """
    ]
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    success = True
    for i, sql in enumerate(sql_commands, 1):
        try:
            print(f"📝 Executing command {i}/{len(sql_commands)}...")
            
            # Use Supabase REST API to execute SQL
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                json={"query": sql.strip()},
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ Command {i} executed successfully")
            else:
                print(f"❌ Command {i} failed: {response.status_code} - {response.text}")
                success = False
                
        except Exception as e:
            print(f"❌ Error executing command {i}: {e}")
            success = False
    
    if success:
        print("\n🎉 Custom prompt templates table setup complete!")
        print("📝 You can now save and manage custom prompt templates in the UI")
    else:
        print("\n⚠️  Some commands failed. You may need to run the SQL manually in Supabase.")
        
    return success

if __name__ == "__main__":
    print("🚀 Setting up custom prompt templates...")
    setup_custom_prompt_templates()