#!/usr/bin/env python3
"""
Setup database tables for RanchEye-02-Analysis

This script creates all necessary tables for the image analysis service.
It reads from the schema.sql file and executes the SQL commands.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Create and return Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY in environment variables")
        sys.exit(1)
    
    return create_client(url, key)

def read_schema_file() -> str:
    """Read the schema.sql file"""
    schema_path = Path(__file__).parent.parent / 'database' / 'schema.sql'
    
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        sys.exit(1)
    
    with open(schema_path, 'r') as f:
        return f.read()

def execute_sql_statements(client: Client, sql: str):
    """Execute SQL statements via Supabase"""
    # Note: Supabase Python client doesn't directly support raw SQL execution
    # This is a placeholder - you'll need to execute these via Supabase dashboard
    # or use a direct PostgreSQL connection
    
    logger.warning("⚠️  Direct SQL execution not available via Supabase Python client")
    logger.info("Please execute the following SQL in your Supabase SQL editor:")
    logger.info("-" * 80)
    print(sql)
    logger.info("-" * 80)
    
    logger.info("\n📝 Steps to create tables:")
    logger.info("1. Go to your Supabase project dashboard")
    logger.info("2. Navigate to SQL Editor")
    logger.info("3. Create a new query")
    logger.info("4. Paste the SQL above")
    logger.info("5. Click 'Run' to execute")
    
    # Alternative: Check if tables exist
    try:
        # Try to query a table to see if it exists
        result = client.table('analysis_configs').select('id').limit(1).execute()
        logger.info("✅ Table 'analysis_configs' already exists")
    except Exception as e:
        logger.info("❌ Table 'analysis_configs' does not exist - please create it")

def create_sample_configs(client: Client):
    """Create sample analysis configurations"""
    sample_configs = [
        {
            'name': 'Main Gate Monitor',
            'analysis_type': 'gate_detection',
            'model_provider': 'openai',
            'model_name': 'gpt-4-vision-preview',
            'prompt_template': '''Analyze this trail camera image and determine if a gate is visible. If a gate is visible, determine if it is OPEN or CLOSED. Respond with a JSON object containing: {"gate_visible": boolean, "gate_open": boolean, "confidence": float between 0-1, "reasoning": "brief explanation"}''',
            'threshold': 0.85
        },
        {
            'name': 'Water Trough Monitor',
            'analysis_type': 'water_level',
            'model_provider': 'openai',
            'model_name': 'gpt-4-vision-preview',
            'prompt_template': '''Analyze this trail camera image for water troughs or containers. Estimate the water level as: FULL (80-100%), ADEQUATE (40-80%), LOW (10-40%), or EMPTY (0-10%). Respond with JSON: {"water_visible": boolean, "water_level": "FULL|ADEQUATE|LOW|EMPTY", "percentage_estimate": number, "confidence": float, "reasoning": "explanation"}''',
            'threshold': 0.80
        }
    ]
    
    logger.info("\n📋 Sample configurations to add (optional):")
    for config in sample_configs:
        logger.info(f"  - {config['name']} ({config['analysis_type']})")
    
    response = input("\nWould you like to create sample configurations? (y/n): ")
    if response.lower() == 'y':
        try:
            for config in sample_configs:
                result = client.table('analysis_configs').insert(config).execute()
                logger.info(f"✅ Created config: {config['name']}")
        except Exception as e:
            logger.warning(f"Could not create sample configs: {e}")
            logger.info("You can create them manually later")

def main():
    """Main setup function"""
    logger.info("🚀 RanchEye-02-Analysis Database Setup")
    logger.info("=" * 80)
    
    # Get Supabase client
    client = get_supabase_client()
    logger.info("✅ Connected to Supabase")
    
    # Read schema
    schema_sql = read_schema_file()
    logger.info("✅ Loaded database schema")
    
    # Execute SQL (or display it)
    execute_sql_statements(client, schema_sql)
    
    # Optionally create sample configs
    logger.info("\n" + "=" * 80)
    create_sample_configs(client)
    
    logger.info("\n✅ Setup complete!")
    logger.info("\n📝 Next steps:")
    logger.info("1. Ensure all tables are created in Supabase")
    logger.info("2. Configure your analysis rules in the 'analysis_configs' table")
    logger.info("3. Run 'python -m src.analyzer' to start processing images")

if __name__ == "__main__":
    main()