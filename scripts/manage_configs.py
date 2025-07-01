#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client
from src.db.supabase_client import SupabaseClient


load_dotenv()


class ConfigManager:
    def __init__(self):
        self.supabase = SupabaseClient(
            url=os.getenv('SUPABASE_URL'),
            key=os.getenv('SUPABASE_KEY')
        )
        
    def create_default_configs(self):
        """Create default analysis configurations for common ranch monitoring scenarios"""
        
        configs = [
            {
                "name": "Gate Detection - All Cameras",
                "camera_name": None,  # Applies to all cameras
                "analysis_type": "gate_detection",
                "model_provider": "openai",
                "model_name": "gpt-4o-mini",
                "prompt_template": """Analyze this ranch camera image and determine if a gate is visible. If a gate is visible, determine if it is OPEN or CLOSED.

Respond with a JSON object containing:
{
  "gate_visible": boolean,
  "gate_open": boolean (null if no gate visible),
  "confidence": float between 0-1,
  "reasoning": "brief explanation of what you see"
}

Be careful to distinguish between:
- Open gates (you can see through/past them)
- Closed gates (blocking the path)
- No gate visible in the image""",
                "threshold": 0.85,
                "alert_cooldown_minutes": 60
            },
            {
                "name": "Water Trough Monitor",
                "camera_name": None,
                "analysis_type": "water_level",
                "model_provider": "openai",
                "model_name": "gpt-4o-mini",
                "prompt_template": """Analyze this ranch camera image for water troughs, tanks, or containers. Estimate the water level.

Respond with JSON:
{
  "water_visible": boolean,
  "water_level": "FULL|ADEQUATE|LOW|EMPTY|UNKNOWN",
  "percentage_estimate": number (0-100, null if unknown),
  "confidence": float (0-1),
  "container_type": "trough|tank|pond|other|none",
  "reasoning": "what you observe about the water source"
}

Water levels:
- FULL: 80-100% capacity
- ADEQUATE: 40-80% capacity  
- LOW: 10-40% capacity (needs attention)
- EMPTY: 0-10% capacity (urgent)""",
                "threshold": 0.80,
                "alert_cooldown_minutes": 120
            },
            {
                "name": "Feed Bin Monitor",
                "camera_name": None,
                "analysis_type": "feed_bin",
                "model_provider": "openai",
                "model_name": "gpt-4o-mini",
                "prompt_template": """Analyze this ranch camera image for feed bins, feeders, or hay storage. Assess the feed level.

Respond with JSON:
{
  "feeder_visible": boolean,
  "feed_level": "FULL|ADEQUATE|LOW|EMPTY|UNKNOWN",
  "percentage_estimate": number (0-100, null if unknown),
  "feed_type": "grain|hay|mineral|mixed|unknown",
  "confidence": float (0-1),
  "animals_present": boolean,
  "reasoning": "observations about the feed situation"
}

Feed levels:
- FULL: 80-100% capacity
- ADEQUATE: 40-80% capacity
- LOW: 10-40% capacity (needs refill soon)
- EMPTY: 0-10% capacity (urgent refill needed)""",
                "threshold": 0.80,
                "alert_cooldown_minutes": 240
            },
            {
                "name": "Animal Detection",
                "camera_name": None,
                "analysis_type": "animal_detection", 
                "model_provider": "openai",
                "model_name": "gpt-4o-mini",
                "prompt_template": """Analyze this ranch camera image for any animals. Identify livestock vs wildlife.

Respond with JSON:
{
  "animals_detected": boolean,
  "animals": [
    {
      "species": "cattle|horse|sheep|goat|deer|hog|bird|other|unknown",
      "count": number,
      "type": "livestock|wildlife|pet|unknown",
      "behavior": "grazing|resting|moving|drinking|other",
      "confidence": float (0-1)
    }
  ],
  "total_count": number,
  "unusual_activity": boolean,
  "reasoning": "description of what you observe"
}""",
                "threshold": 0.75,
                "alert_cooldown_minutes": 30
            }
        ]
        
        # Create configs with dual-model analysis for critical items
        critical_configs = []
        for config in configs[:2]:  # Gate and Water are critical
            # Create a high-accuracy version with dual models
            dual_config = config.copy()
            dual_config["name"] += " - Dual Model"
            dual_config["secondary_provider"] = "openai"
            dual_config["secondary_model"] = "gpt-4o"  # Use better model as secondary
            dual_config["tiebreaker_provider"] = "openai"
            dual_config["tiebreaker_model"] = "gpt-4o"
            critical_configs.append(dual_config)
            
            # Create a cross-provider version with Gemini
            cross_config = config.copy()
            cross_config["name"] += " - Cross-Provider (Gemini)"
            cross_config["secondary_provider"] = "gemini"
            cross_config["secondary_model"] = "gemini-1.5-flash"
            cross_config["tiebreaker_provider"] = "gemini"
            cross_config["tiebreaker_model"] = "gemini-1.5-pro"
            critical_configs.append(cross_config)
        
        all_configs = configs + critical_configs
        
        # Insert configs
        created_count = 0
        for config in all_configs:
            try:
                result = self.supabase.client.table('analysis_configs').insert(config).execute()
                print(f"Created config: {config['name']}")
                created_count += 1
            except Exception as e:
                print(f"Error creating config '{config['name']}': {e}")
        
        print(f"\nCreated {created_count} configurations")
        return created_count
    
    def list_configs(self):
        """List all analysis configurations"""
        try:
            response = self.supabase.client.table('analysis_configs').select('*').order('created_at').execute()
            configs = response.data
            
            print(f"\nFound {len(configs)} configurations:\n")
            
            for config in configs:
                status = "ACTIVE" if config['active'] else "INACTIVE"
                print(f"ID: {config['id']}")
                print(f"Name: {config['name']} [{status}]")
                print(f"Type: {config['analysis_type']}")
                print(f"Camera: {config['camera_name'] or 'All cameras'}")
                print(f"Model: {config['model_provider']}/{config['model_name']}")
                if config.get('secondary_provider'):
                    print(f"Secondary: {config['secondary_provider']}/{config['secondary_model']}")
                print(f"Threshold: {config['threshold']}")
                print(f"Created: {config['created_at']}")
                print("-" * 50)
                
        except Exception as e:
            print(f"Error listing configs: {e}")
    
    def toggle_config(self, config_id: str, active: bool = None):
        """Enable or disable a configuration"""
        try:
            if active is None:
                # Toggle current state
                response = self.supabase.client.table('analysis_configs').select('active').eq('id', config_id).single().execute()
                active = not response.data['active']
            
            self.supabase.client.table('analysis_configs').update({
                'active': active,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', config_id).execute()
            
            print(f"Config {config_id} is now {'ACTIVE' if active else 'INACTIVE'}")
            
        except Exception as e:
            print(f"Error toggling config: {e}")
    
    def create_camera_specific_config(self, camera_name: str, analysis_type: str):
        """Create a configuration for a specific camera"""
        # Get a template config
        response = self.supabase.client.table('analysis_configs').select('*').eq(
            'analysis_type', analysis_type
        ).is_('camera_name', 'null').limit(1).execute()
        
        if not response.data:
            print(f"No template found for analysis type: {analysis_type}")
            return
        
        template = response.data[0]
        
        # Create camera-specific version
        new_config = {
            "name": f"{template['name']} - {camera_name}",
            "camera_name": camera_name,
            "analysis_type": template['analysis_type'],
            "model_provider": template['model_provider'],
            "model_name": template['model_name'],
            "prompt_template": template['prompt_template'],
            "threshold": template['threshold'],
            "alert_cooldown_minutes": template['alert_cooldown_minutes']
        }
        
        if template.get('secondary_provider'):
            new_config['secondary_provider'] = template['secondary_provider']
            new_config['secondary_model'] = template['secondary_model']
        
        try:
            self.supabase.client.table('analysis_configs').insert(new_config).execute()
            print(f"Created camera-specific config: {new_config['name']}")
        except Exception as e:
            print(f"Error creating camera config: {e}")


def main():
    manager = ConfigManager()
    
    if len(sys.argv) < 2:
        print("Usage: python manage_configs.py [command] [args]")
        print("\nCommands:")
        print("  create-defaults     - Create default analysis configurations")
        print("  list               - List all configurations")
        print("  enable <id>        - Enable a configuration")
        print("  disable <id>       - Disable a configuration")
        print("  toggle <id>        - Toggle a configuration")
        print("  camera <name> <type> - Create camera-specific config")
        return
    
    command = sys.argv[1]
    
    if command == "create-defaults":
        manager.create_default_configs()
    elif command == "list":
        manager.list_configs()
    elif command == "enable" and len(sys.argv) > 2:
        manager.toggle_config(sys.argv[2], active=True)
    elif command == "disable" and len(sys.argv) > 2:
        manager.toggle_config(sys.argv[2], active=False)
    elif command == "toggle" and len(sys.argv) > 2:
        manager.toggle_config(sys.argv[2])
    elif command == "camera" and len(sys.argv) > 3:
        manager.create_camera_specific_config(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()