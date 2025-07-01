import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import logging
import uuid
from ..providers.base import BaseProvider, ImageData, AnalysisResult
from ..providers.provider_factory import ProviderFactory
from ..db.supabase_client import SupabaseClient


logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.providers: Dict[str, BaseProvider] = {}
        
    def _get_provider(self, provider_name: str, api_key: str) -> BaseProvider:
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderFactory.create_provider(
                provider_name, 
                api_key
            )
        return self.providers[provider_name]
    
    async def _save_analysis_log(
        self,
        image_data: ImageData,
        config: Dict[str, Any],
        prompt: str,
        result: AnalysisResult,
        session_id: Optional[str] = None,
        user_initiated: bool = False,
        task_id: Optional[str] = None,
        custom_prompt: bool = False
    ) -> Optional[str]:
        """Save comprehensive analysis log for audit trail"""
        try:
            # Determine if this was a custom prompt
            is_custom = custom_prompt or (prompt != config.get('prompt_template', ''))
            
            return await self.supabase.save_ai_analysis_log(
                image_id=image_data.image_id,
                image_url=getattr(image_data, 'image_url', None),
                camera_name=image_data.camera_name,
                captured_at=image_data.captured_at,
                analysis_type=config.get('analysis_type', 'unknown'),
                prompt_text=prompt,
                custom_prompt=is_custom,
                model_provider=result.provider,
                model_name=result.model,
                raw_response=result.raw_response,
                parsed_response=result.parsed_data,
                confidence=result.confidence,
                analysis_successful=result.error is None,
                error_message=result.error,
                processing_time_ms=result.processing_time_ms,
                tokens_used=result.tokens_used,
                config_id=config.get('id'),
                task_id=task_id,
                session_id=session_id,
                user_initiated=user_initiated,
                model_temperature=getattr(result, 'temperature', 0.3),
                max_tokens=getattr(result, 'max_tokens', 500)
            )
        except Exception as e:
            logger.error(f"Failed to save analysis log: {e}")
            return None
    
    async def analyze_with_dual_models(
        self,
        image_data: ImageData,
        config: Dict[str, Any],
        primary_provider_key: str,
        secondary_provider_key: Optional[str] = None,
        tiebreaker_provider_key: Optional[str] = None,
        session_id: Optional[str] = None,
        user_initiated: bool = False,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        
        primary_provider = self._get_provider(
            config['primary_provider'],
            primary_provider_key
        )
        
        # Generate session ID if not provided (for grouping related analyses)
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Run primary analysis with appropriate max_tokens for the model
        max_tokens = 1000 if config['primary_provider'] == 'gemini' else 500
        primary_result = await primary_provider.analyze_image(
            image_data,
            config['prompt_template'],
            config['primary_model'],
            max_tokens=max_tokens
        )
        
        # Save primary analysis log
        await self._save_analysis_log(
            image_data, config, config['prompt_template'], primary_result,
            session_id, user_initiated, task_id
        )
        
        # If no secondary model configured, return primary result
        if not config.get('secondary_provider') or not secondary_provider_key:
            return {
                'primary_result': primary_result,
                'secondary_result': None,
                'final_result': primary_result.parsed_data,
                'agreement': True,
                'tiebreaker_used': False
            }
        
        # Run secondary analysis
        secondary_provider = self._get_provider(
            config['secondary_provider'],
            secondary_provider_key
        )
        
        secondary_max_tokens = 1000 if config['secondary_provider'] == 'gemini' else 500
        secondary_result = await secondary_provider.analyze_image(
            image_data,
            config['prompt_template'],
            config['secondary_model'],
            max_tokens=secondary_max_tokens
        )
        
        # Save secondary analysis log
        await self._save_analysis_log(
            image_data, config, config['prompt_template'], secondary_result,
            session_id, user_initiated, task_id
        )
        
        # Check for agreement
        agreement = self._check_agreement(
            primary_result.parsed_data,
            secondary_result.parsed_data,
            config['analysis_type']
        )
        
        if agreement:
            return {
                'primary_result': primary_result,
                'secondary_result': secondary_result,
                'final_result': primary_result.parsed_data,
                'agreement': True,
                'tiebreaker_used': False
            }
        
        # Disagreement - use tiebreaker if configured
        if config.get('tiebreaker_provider') and tiebreaker_provider_key:
            tiebreaker_provider = self._get_provider(
                config['tiebreaker_provider'],
                tiebreaker_provider_key
            )
            
            tiebreaker_prompt = self._create_tiebreaker_prompt(
                config['prompt_template'],
                primary_result.parsed_data,
                secondary_result.parsed_data
            )
            
            tiebreaker_max_tokens = 1000 if config['tiebreaker_provider'] == 'gemini' else 500
            tiebreaker_result = await tiebreaker_provider.analyze_image(
                image_data,
                tiebreaker_prompt,
                config['tiebreaker_model'],
                max_tokens=tiebreaker_max_tokens
            )
            
            # Save tiebreaker analysis log
            await self._save_analysis_log(
                image_data, config, tiebreaker_prompt, tiebreaker_result,
                session_id, user_initiated, task_id, custom_prompt=True
            )
            
            return {
                'primary_result': primary_result,
                'secondary_result': secondary_result,
                'tiebreaker_result': tiebreaker_result,
                'final_result': tiebreaker_result.parsed_data,
                'agreement': False,
                'tiebreaker_used': True
            }
        
        # No tiebreaker - use higher confidence result
        if primary_result.confidence >= secondary_result.confidence:
            final_result = primary_result.parsed_data
        else:
            final_result = secondary_result.parsed_data
            
        return {
            'primary_result': primary_result,
            'secondary_result': secondary_result,
            'final_result': final_result,
            'agreement': False,
            'tiebreaker_used': False
        }
    
    def _check_agreement(
        self, 
        result1: Dict[str, Any], 
        result2: Dict[str, Any],
        analysis_type: str
    ) -> bool:
        if analysis_type == 'gate_detection':
            return (
                result1.get('gate_visible') == result2.get('gate_visible') and
                result1.get('gate_open') == result2.get('gate_open')
            )
        elif analysis_type == 'water_level':
            return result1.get('water_level') == result2.get('water_level')
        elif analysis_type == 'feed_bin':
            return result1.get('feed_level') == result2.get('feed_level')
        else:
            # For custom analysis, check if main conclusions match
            return result1.get('conclusion') == result2.get('conclusion')
    
    def _create_tiebreaker_prompt(
        self,
        original_prompt: str,
        result1: Dict[str, Any],
        result2: Dict[str, Any]
    ) -> str:
        return f"""{original_prompt}

Two AI models have analyzed this image with different results:

Model 1 Result: {json.dumps(result1, indent=2)}

Model 2 Result: {json.dumps(result2, indent=2)}

Please analyze the image independently and provide your assessment. Consider both previous results but make your own determination based on what you see in the image."""
    
    async def process_analysis_task(
        self,
        task_id: str,
        api_keys: Dict[str, str]
    ) -> bool:
        try:
            # Get task details
            task = await self.supabase.get_analysis_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            # Get analysis config
            config = await self.supabase.get_analysis_config(task['config_id'])
            if not config:
                logger.error(f"Config {task['config_id']} not found")
                return False
            
            # Get image data
            image_metadata = await self.supabase.get_image_metadata(task['image_id'])
            if not image_metadata:
                logger.error(f"Image {task['image_id']} not found")
                return False
            
            # Download image from storage
            image_bytes = await self.supabase.download_image(image_metadata['storage_path'])
            
            image_data = ImageData(
                image_bytes=image_bytes,
                image_id=task['image_id'],
                camera_name=image_metadata['camera_name'],
                captured_at=image_metadata['captured_at']
            )
            
            # Update task status to processing
            await self.supabase.update_task_status(task_id, 'processing')
            
            # Run analysis
            primary_key = api_keys.get(config['primary_provider'].upper() + '_API_KEY')
            secondary_key = api_keys.get(config.get('secondary_provider', '').upper() + '_API_KEY')
            tiebreaker_key = api_keys.get(config.get('tiebreaker_provider', '').upper() + '_API_KEY')
            
            results = await self.analyze_with_dual_models(
                image_data,
                config,
                primary_key,
                secondary_key,
                tiebreaker_key
            )
            
            # Calculate total tokens and cost
            total_tokens = results['primary_result'].tokens_used
            if results.get('secondary_result'):
                total_tokens += results['secondary_result'].tokens_used
            if results.get('tiebreaker_result'):
                total_tokens += results['tiebreaker_result'].tokens_used
            
            # Save results
            await self.supabase.save_analysis_result({
                'image_id': task['image_id'],
                'config_id': task['config_id'],
                'model_provider': config['primary_provider'],
                'model_name': config['primary_model'],
                'analysis_type': config['analysis_type'],
                'result': results['final_result'],
                'confidence': results['final_result'].get('confidence', 0.5),
                'alert_triggered': self._should_trigger_alert(
                    results['final_result'],
                    config
                ),
                'processing_time_ms': results['primary_result'].processing_time_ms,
                'tokens_used': total_tokens,
                'full_results': results  # Store complete analysis data
            })
            
            # Update task status
            await self.supabase.update_task_status(task_id, 'completed')
            
            # Check for alerts
            if self._should_trigger_alert(results['final_result'], config):
                await self._create_alert(
                    results['final_result'],
                    config,
                    image_metadata
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            await self.supabase.update_task_status(
                task_id, 
                'failed',
                error_message=str(e)
            )
            return False
    
    def _should_trigger_alert(
        self,
        result: Dict[str, Any],
        config: Dict[str, Any]
    ) -> bool:
        threshold = config.get('threshold', 0.8)
        confidence = result.get('confidence', 0)
        
        if confidence < threshold:
            return False
        
        if config['analysis_type'] == 'gate_detection':
            return result.get('gate_visible') and result.get('gate_open', False)
        elif config['analysis_type'] == 'water_level':
            level = result.get('water_level', 'ADEQUATE')
            return level in ['LOW', 'EMPTY']
        elif config['analysis_type'] == 'feed_bin':
            level = result.get('feed_level', 'ADEQUATE')
            return level in ['LOW', 'EMPTY']
        else:
            return result.get('alert_condition', False)
    
    async def _create_alert(
        self,
        result: Dict[str, Any],
        config: Dict[str, Any],
        image_metadata: Dict[str, Any]
    ) -> None:
        alert_type = 'immediate' if result.get('confidence', 0) > 0.9 else 'warning'
        
        if config['analysis_type'] == 'gate_detection':
            title = f"Gate Open Alert - {image_metadata['camera_name']}"
            message = f"Gate detected as OPEN with {result.get('confidence', 0)*100:.0f}% confidence"
        elif config['analysis_type'] == 'water_level':
            title = f"Low Water Alert - {image_metadata['camera_name']}"
            message = f"Water level: {result.get('water_level')} ({result.get('percentage_estimate', 0)}%)"
        elif config['analysis_type'] == 'feed_bin':
            title = f"Low Feed Alert - {image_metadata['camera_name']}"
            message = f"Feed level: {result.get('feed_level')} ({result.get('percentage_estimate', 0)}%)"
        else:
            title = f"Alert - {image_metadata['camera_name']}"
            message = result.get('alert_message', 'Condition detected')
        
        await self.supabase.create_alert({
            'alert_type': alert_type,
            'severity': 'critical' if alert_type == 'immediate' else 'warning',
            'title': title,
            'message': message,
            'camera_name': image_metadata['camera_name'],
            'image_url': image_metadata.get('image_url'),
            'alert_data': result
        })