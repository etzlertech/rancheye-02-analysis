#!/usr/bin/env python3
"""
RanchEye-02-Analysis
Main entry point for the ranch camera AI analysis system
"""
import asyncio
import sys
import os
from src.task_processor import TaskProcessor
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    print("""
    RanchEye-02 Analysis System
    ==========================
    
    AI-powered ranch monitoring for:
    - Gate status (open/closed)
    - Water trough levels
    - Feed bin status
    - Animal detection
    
    Starting analysis processor...
    """)
    
    processor = TaskProcessor()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Run test suite
            os.system("python scripts/test_analysis.py")
            return
        elif sys.argv[1] == "--setup":
            # Create default configurations
            os.system("python scripts/manage_configs.py create-defaults")
            return
        elif sys.argv[1] == "--list-configs":
            # List configurations
            os.system("python scripts/manage_configs.py list")
            return
        elif sys.argv[1] == "--help":
            print("""
Usage:
    python main.py              - Run continuous analysis processing
    python main.py IMAGE_ID     - Process a specific image
    python main.py --test       - Run system tests
    python main.py --setup      - Create default configurations
    python main.py --list-configs - List all configurations
    python main.py --help       - Show this help
            """)
            return
        else:
            # Process specific image
            image_id = sys.argv[1]
            print(f"Processing single image: {image_id}")
            success = await processor.process_single_image(image_id)
            return 0 if success else 1
    
    # Run continuous processing
    await processor.run_continuous()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)