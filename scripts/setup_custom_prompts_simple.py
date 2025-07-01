#!/usr/bin/env python3
"""
Simple script to display SQL for creating custom_prompt_templates table
Since the Management API has issues with complex SQL, this script outputs
the SQL for manual execution in Supabase SQL Editor
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main function to display SQL"""
    logger.info("🚀 Custom Prompt Templates Table Setup")
    logger.info("=" * 80)
    
    # Get Supabase URL for reference
    supabase_url = os.getenv('SUPABASE_URL', 'your-supabase-url')
    project_id = os.getenv('SUPABASE_PROJECT_ID', 'your-project-id')
    
    logger.info(f"\nProject URL: {supabase_url}")
    logger.info(f"Project ID: {project_id}")
    
    # Read SQL file
    sql_file = Path(__file__).parent.parent / 'database' / 'custom_prompt_templates.sql'
    
    if not sql_file.exists():
        logger.error(f"SQL file not found at {sql_file}")
        return
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    logger.info("\n📝 INSTRUCTIONS:")
    logger.info("=" * 50)
    logger.info("1. Go to your Supabase project dashboard")
    logger.info("2. Navigate to SQL Editor (in the left sidebar)")
    logger.info("3. Click 'New query'")
    logger.info("4. Copy and paste the SQL below")
    logger.info("5. Click 'Run' to execute")
    logger.info("\n" + "=" * 50)
    logger.info("SQL TO EXECUTE:")
    logger.info("=" * 50 + "\n")
    
    print(sql_content)
    
    logger.info("\n" + "=" * 50)
    logger.info("\n✅ After running the SQL, you should have:")
    logger.info("   - custom_prompt_templates table")
    logger.info("   - All necessary indexes")
    logger.info("   - Helper functions (increment_prompt_usage, set_default_template)")
    logger.info("   - Update trigger for updated_at timestamp")
    logger.info("   - active_prompt_templates view")
    logger.info("   - 5 default system templates")
    
    logger.info("\n🔍 To verify the setup, run this query:")
    logger.info("   SELECT * FROM custom_prompt_templates WHERE is_system = true;")
    
    logger.info("\n📺 Direct link to SQL Editor:")
    if 'supabase.co' in supabase_url:
        dashboard_url = supabase_url.replace('https://', 'https://app.supabase.com/project/').split('.')[0]
        logger.info(f"   {dashboard_url}/sql/new")

if __name__ == "__main__":
    main()