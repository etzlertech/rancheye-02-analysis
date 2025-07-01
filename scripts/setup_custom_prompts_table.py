#!/usr/bin/env python3
"""
Setup custom_prompt_templates table in Supabase
This script creates the custom prompt templates table and all related functions
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class CustomPromptsTableSetup:
    """Setup custom_prompt_templates table via Supabase Management API"""
    
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
            logger.error(f"Error {response.status_code}: {response.text}")
            return None
        
        return response.json() if response.text else {}
    
    def run_sql_query(self, query: str) -> Dict:
        """Execute SQL query via API"""
        return self._request("POST", f"/projects/{self.project_id}/database/query", {
            "query": query
        })
    
    def setup_custom_prompts_table(self):
        """Create the custom_prompt_templates table and related objects"""
        logger.info("Setting up custom_prompt_templates table...")
        
        # Read SQL file
        sql_file = Path(__file__).parent.parent / 'database' / 'custom_prompt_templates.sql'
        
        if not sql_file.exists():
            logger.error(f"SQL file not found at {sql_file}")
            return False
        
        with open(sql_file, 'r') as f:
            full_sql = f.read()
        
        # Split SQL into individual statements
        # This is a simple split - for production, use a proper SQL parser
        statements = []
        current_statement = []
        
        for line in full_sql.split('\n'):
            # Skip comments and empty lines
            if line.strip().startswith('--') or not line.strip():
                continue
            
            current_statement.append(line)
            
            # Check if this line ends a statement
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement)
                statements.append(statement)
                current_statement = []
        
        # Execute each statement
        success_count = 0
        total_count = len(statements)
        
        for i, statement in enumerate(statements, 1):
            # Get a description of what we're doing
            if 'CREATE TABLE' in statement:
                description = "Creating custom_prompt_templates table"
            elif 'CREATE INDEX' in statement:
                index_match = statement.split('CREATE INDEX')[1].split(' ON ')[0].strip()
                description = f"Creating index {index_match}"
            elif 'CREATE OR REPLACE FUNCTION' in statement:
                func_match = statement.split('FUNCTION')[1].split('(')[0].strip()
                description = f"Creating function {func_match}"
            elif 'CREATE TRIGGER' in statement:
                trigger_match = statement.split('CREATE TRIGGER')[1].split(' ')[0].strip()
                description = f"Creating trigger {trigger_match}"
            elif 'CREATE OR REPLACE VIEW' in statement:
                view_match = statement.split('VIEW')[1].split(' AS')[0].strip()
                description = f"Creating view {view_match}"
            elif 'INSERT INTO' in statement:
                description = "Inserting default system templates"
            else:
                description = f"Executing statement {i}"
            
            logger.info(f"[{i}/{total_count}] {description}...")
            
            result = self.run_sql_query(statement)
            if result is not None:
                success_count += 1
                logger.info(f"  ✓ Success")
            else:
                logger.error(f"  ✗ Failed")
                # Log the failed statement for debugging
                logger.debug(f"Failed statement:\n{statement[:200]}...")
        
        logger.info(f"\nCompleted: {success_count}/{total_count} statements executed successfully")
        return success_count == total_count
    
    def verify_table_exists(self):
        """Verify the table was created successfully"""
        logger.info("\nVerifying table creation...")
        
        # Check if table exists
        check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'custom_prompt_templates'
        );
        """
        
        result = self.run_sql_query(check_query)
        if result and result.get('data'):
            exists = result['data'][0].get('exists', False)
            if exists:
                logger.info("✓ Table 'custom_prompt_templates' exists")
                
                # Count default templates
                count_query = """
                SELECT COUNT(*) as count 
                FROM custom_prompt_templates 
                WHERE is_system = true;
                """
                
                count_result = self.run_sql_query(count_query)
                if count_result and count_result.get('data'):
                    count = count_result['data'][0].get('count', 0)
                    logger.info(f"✓ Found {count} system templates")
                
                return True
            else:
                logger.error("✗ Table 'custom_prompt_templates' does not exist")
                return False
        
        logger.error("✗ Could not verify table existence")
        return False
    
    def show_sample_usage(self):
        """Show how to use the custom prompts table"""
        logger.info("\n📝 SAMPLE USAGE:")
        logger.info("=" * 50)
        
        logger.info("\n1. Query default templates:")
        logger.info("   SELECT * FROM custom_prompt_templates WHERE is_default = true;")
        
        logger.info("\n2. Create a custom template:")
        logger.info("""   INSERT INTO custom_prompt_templates (
       name, description, prompt_text, analysis_type
   ) VALUES (
       'My Custom Gate Detector',
       'Enhanced gate detection with weather consideration',
       'Analyze the gate and also note weather conditions...',
       'gate_detection'
   );""")
        
        logger.info("\n3. Set a template as default:")
        logger.info("   SELECT set_default_template('template-uuid-here');")
        
        logger.info("\n4. Track template usage:")
        logger.info("   SELECT increment_prompt_usage('template-uuid-here');")
        
        logger.info("\n5. View active templates with stats:")
        logger.info("   SELECT * FROM active_prompt_templates;")

def main():
    """Main setup function"""
    logger.info("🚀 Custom Prompt Templates Table Setup")
    logger.info("=" * 80)
    
    try:
        setup = CustomPromptsTableSetup()
        
        # Create table and related objects
        if setup.setup_custom_prompts_table():
            logger.info("\n✅ Table setup completed successfully!")
            
            # Verify creation
            if setup.verify_table_exists():
                logger.info("\n✅ Table verification passed!")
                
                # Show usage examples
                setup.show_sample_usage()
                
                logger.info("\n✅ Custom prompt templates are ready to use!")
                logger.info("\nNext steps:")
                logger.info("1. Access your templates via the Supabase client")
                logger.info("2. Use the web interface to create and manage custom prompts")
                logger.info("3. Templates will be automatically used by the analysis system")
            else:
                logger.error("\n❌ Table verification failed")
                sys.exit(1)
        else:
            logger.error("\n❌ Table setup failed")
            logger.info("\nTroubleshooting:")
            logger.info("1. Check your SUPABASE_ACCESS_TOKEN is valid")
            logger.info("2. Ensure you have database admin permissions")
            logger.info("3. Try running the SQL manually in Supabase SQL Editor")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ Setup failed: {e}")
        logger.info("\nMake sure you have:")
        logger.info("1. SUPABASE_PROJECT_ID in your .env file")
        logger.info("2. SUPABASE_ACCESS_TOKEN in your .env file")
        logger.info("3. Valid permissions to create tables")
        sys.exit(1)

if __name__ == "__main__":
    main()