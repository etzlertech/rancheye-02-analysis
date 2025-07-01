#!/usr/bin/env python3
"""
Direct database setup for custom_prompt_templates using psycopg2
This connects directly to the Supabase PostgreSQL database
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DirectDatabaseSetup:
    """Setup custom_prompt_templates table via direct PostgreSQL connection"""
    
    def __init__(self):
        # Parse Supabase URL to get database connection details
        supabase_url = os.getenv('SUPABASE_URL')
        if not supabase_url:
            raise ValueError("SUPABASE_URL not found in environment variables")
        
        # Extract project ID from URL
        parsed = urlparse(supabase_url)
        project_id = parsed.hostname.split('.')[0]
        
        # Construct database connection string
        # Supabase PostgreSQL format: postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
        self.db_host = f"db.{project_id}.supabase.co"
        self.db_port = 5432
        self.db_name = "postgres"
        self.db_user = "postgres"
        self.db_password = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Often the service role key works
        
        # Alternative: Use direct database password if provided
        if os.getenv('SUPABASE_DB_PASSWORD'):
            self.db_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    def get_connection(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            logger.info("\n⚠️  Direct database connection failed.")
            logger.info("This is expected - Supabase doesn't allow direct connections by default.")
            logger.info("\nPlease use one of these methods instead:")
            logger.info("1. Run the SQL in Supabase SQL Editor (recommended)")
            logger.info("2. Use the Supabase CLI")
            logger.info("3. Enable direct connections in Supabase settings")
            return None
    
    def setup_table(self):
        """Create the custom_prompt_templates table"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            # Read SQL file
            sql_file = Path(__file__).parent.parent / 'database' / 'custom_prompt_templates.sql'
            
            if not sql_file.exists():
                logger.error(f"SQL file not found at {sql_file}")
                return False
            
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Execute the entire SQL file
            with conn.cursor() as cursor:
                cursor.execute(sql_content)
                conn.commit()
            
            logger.info("✅ Successfully created custom_prompt_templates table and all related objects!")
            
            # Verify the setup
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM custom_prompt_templates WHERE is_system = true;")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Inserted {count} default system templates")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def main():
    """Main setup function"""
    logger.info("🚀 Custom Prompt Templates Direct Database Setup")
    logger.info("=" * 80)
    
    setup = DirectDatabaseSetup()
    
    if setup.setup_table():
        logger.info("\n✅ Setup completed successfully!")
        logger.info("\nThe custom_prompt_templates table is now ready to use.")
        logger.info("\nYou can now:")
        logger.info("1. Use the web interface to create and manage custom prompts")
        logger.info("2. Access templates via the Supabase client in your application")
        logger.info("3. View templates in the Supabase dashboard table editor")
    else:
        logger.info("\n❌ Direct setup failed.")
        logger.info("\nPlease run the SQL manually:")
        logger.info("1. Run: python scripts/setup_custom_prompts_simple.py")
        logger.info("2. Copy the SQL output")
        logger.info("3. Paste and run in Supabase SQL Editor")

if __name__ == "__main__":
    main()