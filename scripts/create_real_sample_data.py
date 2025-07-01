#!/usr/bin/env python3
"""
Create real sample data for testing
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

def main():
    # Create client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    client = create_client(url, key)
    
    print("🧪 Creating Real Sample Data")
    print("=" * 50)
    
    # Step 1: Create analysis configurations
    print("\n📝 Creating analysis configurations...")
    
    configs = [
        {
            'name': 'Gate Monitor - Main Entrance',
            'camera_name': 'cam-01',
            'analysis_type': 'gate_detection',
            'model_provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'prompt_template': '''Analyze this trail camera image and determine if a gate is visible. If a gate is visible, determine if it is OPEN or CLOSED. 
Respond with a JSON object containing: 
{"gate_visible": boolean, "gate_open": boolean, "confidence": float between 0-1, "reasoning": "brief explanation"}''',
            'threshold': 0.85,
            'active': True
        },
        {
            'name': 'Wildlife Detection - All Cameras',
            'camera_name': None,  # Applies to all cameras
            'analysis_type': 'animal_detection',
            'model_provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'prompt_template': '''Analyze this trail camera image for any animals. Identify the species if possible, count how many, and note if they are livestock or wildlife. 
Respond with JSON: 
{"animals_detected": boolean, "animals": [{"species": "name or unknown", "count": number, "type": "livestock|wildlife|unknown", "confidence": float}], "reasoning": "explanation"}''',
            'threshold': 0.75,
            'active': True
        },
        {
            'name': 'Water Level Monitor',
            'camera_name': 'FLEX-S-DARK-GTM7',
            'analysis_type': 'water_level',
            'model_provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'prompt_template': '''Analyze this trail camera image for water troughs or containers. Estimate the water level as: FULL (80-100%), ADEQUATE (40-80%), LOW (10-40%), or EMPTY (0-10%). 
Respond with JSON: 
{"water_visible": boolean, "water_level": "FULL|ADEQUATE|LOW|EMPTY", "percentage_estimate": number, "confidence": float, "reasoning": "explanation"}''',
            'threshold': 0.80,
            'active': True
        }
    ]
    
    created_configs = []
    for config in configs:
        try:
            result = client.table('analysis_configs').insert(config).execute()
            created_configs.append(result.data[0])
            print(f"  ✓ Created: {config['name']}")
        except Exception as e:
            print(f"  ✗ Error creating {config['name']}: {e}")
    
    # Step 2: Get some real images to analyze
    print("\n🖼️  Getting recent images...")
    try:
        images = client.table('spypoint_images').select('image_id, camera_name').order('downloaded_at', desc=True).limit(10).execute()
        print(f"  Found {len(images.data)} recent images")
    except Exception as e:
        print(f"  ✗ Error getting images: {e}")
        return
    
    # Step 3: Create analysis tasks for these images
    print("\n📋 Creating analysis tasks...")
    task_count = 0
    
    for image in images.data[:5]:  # Just use first 5 images
        for config in created_configs:
            # Check if config applies to this camera
            if config['camera_name'] is None or config['camera_name'] == image['camera_name']:
                try:
                    task = {
                        'image_id': image['image_id'],
                        'config_id': config['id'],
                        'status': 'pending',
                        'priority': 5
                    }
                    client.table('analysis_tasks').insert(task).execute()
                    task_count += 1
                except Exception as e:
                    # Likely duplicate, which is fine
                    pass
    
    print(f"  ✓ Created {task_count} analysis tasks")
    
    # Step 4: Show summary
    print("\n📊 Summary:")
    print(f"  - {len(created_configs)} analysis configurations")
    print(f"  - {task_count} pending analysis tasks")
    
    # Show pending tasks by type
    try:
        pending = client.table('analysis_tasks').select(
            'config_id, analysis_configs!inner(analysis_type)'
        ).eq('status', 'pending').execute()
        
        if pending.data:
            type_counts = {}
            for task in pending.data:
                analysis_type = task['analysis_configs']['analysis_type']
                type_counts[analysis_type] = type_counts.get(analysis_type, 0) + 1
            
            print("\n  Pending tasks by type:")
            for atype, count in type_counts.items():
                print(f"    - {atype}: {count}")
    except:
        pass
    
    print("\n✅ Sample data created successfully!")
    print("\n💡 Next steps:")
    print("  1. Start the task processor: python src/task_processor.py")
    print("  2. Or run the web UI: python web_server.py")

if __name__ == "__main__":
    main()