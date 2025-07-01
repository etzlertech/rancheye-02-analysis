#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.db.supabase_client import SupabaseClient
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase
supabase = SupabaseClient(
    url=os.getenv('SUPABASE_URL'),
    key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
)

# Check if spypoint_images table exists and has data
try:
    response = supabase.client.table('spypoint_images').select('*').limit(5).execute()
    print(f'Found {len(response.data)} images in spypoint_images table')
    if response.data:
        print('\nSample image:')
        for key, value in response.data[0].items():
            print(f'  {key}: {value}')
    else:
        print('No images found in spypoint_images table')
        print('\nTrying to insert sample data...')
        
        # Insert sample image
        sample_image = {
            'image_id': 'test-image-001',
            'camera_name': 'Test Camera 1',
            'captured_at': '2025-01-01T12:00:00Z',
            'storage_path': 'images/test-image-001.jpg',
            'metadata': {'test': True}
        }
        
        insert_response = supabase.client.table('spypoint_images').insert(sample_image).execute()
        print('Sample image inserted:', insert_response.data)
        
except Exception as e:
    print(f'Error accessing spypoint_images: {e}')
    print('\nTrying to create the table...')
    
    # Try using the PAT to create the table
    from scripts.execute_sql_with_pat import SupabaseSQL
    
    sql_executor = SupabaseSQL()
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS spypoint_images (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        image_id TEXT UNIQUE NOT NULL,
        camera_name TEXT NOT NULL,
        captured_at TIMESTAMPTZ NOT NULL,
        storage_path TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    result = sql_executor.execute_sql(create_table_sql)
    if result:
        print('Table created successfully')
        
        # Insert sample data
        insert_sql = """
        INSERT INTO spypoint_images (image_id, camera_name, captured_at, storage_path)
        VALUES 
        ('test-001', 'North Gate Camera', NOW() - INTERVAL '1 hour', 'images/test-001.jpg'),
        ('test-002', 'South Pasture Camera', NOW() - INTERVAL '2 hours', 'images/test-002.jpg'),
        ('test-003', 'Water Trough Camera', NOW() - INTERVAL '3 hours', 'images/test-003.jpg');
        """
        
        result = sql_executor.execute_sql(insert_sql)
        if result:
            print('Sample data inserted')
    else:
        print('Failed to create table')