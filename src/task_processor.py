import asyncio
import os
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from .db.supabase_client import SupabaseClient
from .services.analysis_service import AnalysisService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskProcessor:
    def __init__(self):
        load_dotenv()
        
        # Initialize Supabase client
        self.supabase = SupabaseClient(
            url=os.getenv('SUPABASE_URL'),
            key=os.getenv('SUPABASE_KEY')
        )
        
        # Initialize analysis service
        self.analysis_service = AnalysisService(self.supabase)
        
        # Collect API keys
        self.api_keys = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
        }
        
        # Processing settings
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.max_workers = int(os.getenv('MAX_WORKERS', '5'))
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
    async def process_batch(self) -> int:
        # Get pending tasks
        tasks = await self.supabase.get_pending_tasks(self.batch_size)
        
        if not tasks:
            logger.info("No pending tasks found")
            return 0
        
        logger.info(f"Processing {len(tasks)} tasks")
        
        # Process tasks concurrently with limited workers
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_limit(task):
            async with semaphore:
                return await self.analysis_service.process_analysis_task(
                    task['id'],
                    self.api_keys
                )
        
        # Process all tasks
        results = await asyncio.gather(
            *[process_with_limit(task) for task in tasks],
            return_exceptions=True
        )
        
        # Count successful processes
        success_count = sum(1 for r in results if r is True)
        logger.info(f"Successfully processed {success_count}/{len(tasks)} tasks")
        
        return success_count
    
    async def run_continuous(self, interval_minutes: int = None):
        if interval_minutes is None:
            interval_minutes = int(os.getenv('ANALYSIS_INTERVAL_MINUTES', '30'))
        
        logger.info(f"Starting continuous processing with {interval_minutes} minute intervals")
        
        while True:
            try:
                start_time = datetime.utcnow()
                processed = await self.process_batch()
                
                # If we processed a full batch, immediately check for more
                if processed == self.batch_size:
                    logger.info("Full batch processed, checking for more tasks immediately")
                    continue
                
                # Otherwise wait for the interval
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                wait_time = max(0, interval_minutes * 60 - elapsed)
                
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.0f} seconds until next batch")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def process_single_image(self, image_id: str) -> bool:
        # Create analysis tasks for the image
        task_count = await self.supabase.create_analysis_tasks_for_image(image_id)
        logger.info(f"Created {task_count} analysis tasks for image {image_id}")
        
        if task_count == 0:
            return False
        
        # Get the tasks we just created
        tasks = await self.supabase.client.table('analysis_tasks').select('*').eq(
            'image_id', image_id
        ).execute()
        
        # Process each task
        success_count = 0
        for task in tasks.data:
            result = await self.analysis_service.process_analysis_task(
                task['id'],
                self.api_keys
            )
            if result:
                success_count += 1
        
        logger.info(f"Processed {success_count}/{len(tasks.data)} tasks for image {image_id}")
        return success_count > 0


async def main():
    processor = TaskProcessor()
    
    # Check if we should process a specific image
    import sys
    if len(sys.argv) > 1:
        image_id = sys.argv[1]
        logger.info(f"Processing single image: {image_id}")
        success = await processor.process_single_image(image_id)
        return 0 if success else 1
    
    # Otherwise run continuous processing
    await processor.run_continuous()


if __name__ == "__main__":
    asyncio.run(main())