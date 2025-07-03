#!/usr/bin/env python3
"""
Comprehensive audit script for ai_analysis_logs table
Analyzes data patterns, completeness, and multi-model usage
"""

import os
import sys
from datetime import datetime
from collections import defaultdict
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, List, Any
# Remove pandas dependency for simpler execution

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    sys.exit(1)

supabase: Client = create_client(url, key)


def fetch_recent_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch the most recent ai_analysis_logs"""
    try:
        response = supabase.table('ai_analysis_logs').select("*").order(
            'created_at', desc=True
        ).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []


def fetch_logs_by_session() -> Dict[str, List[Dict[str, Any]]]:
    """Fetch logs grouped by session_id"""
    try:
        # Get logs with session_id
        response = supabase.table('ai_analysis_logs').select("*").not_.is_(
            'session_id', 'null'
        ).order('created_at', desc=True).limit(100).execute()
        
        # Group by session_id
        sessions = defaultdict(list)
        for log in response.data:
            sessions[log['session_id']].append(log)
        
        return dict(sessions)
    except Exception as e:
        print(f"Error fetching logs by session: {e}")
        return {}


def analyze_field_completeness(logs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Analyze which fields are populated vs NULL"""
    if not logs:
        return {}
    
    field_stats = {}
    total_records = len(logs)
    
    # Get all fields from first record
    fields = list(logs[0].keys())
    
    for field in fields:
        populated_count = sum(1 for log in logs if log.get(field) is not None)
        null_count = total_records - populated_count
        
        # Get sample values (non-null)
        sample_values = []
        for log in logs:
            if log.get(field) is not None and len(sample_values) < 3:
                value = log[field]
                # Truncate long strings
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                sample_values.append(value)
        
        field_stats[field] = {
            'populated': populated_count,
            'null': null_count,
            'percentage_populated': (populated_count / total_records * 100),
            'sample_values': sample_values
        }
    
    return field_stats


def analyze_multi_model_patterns(sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Analyze how multi-model analyses are tracked"""
    multi_model_sessions = {}
    
    for session_id, logs in sessions.items():
        if len(logs) > 1:
            # Check if multiple models were used
            models_used = set()
            for log in logs:
                model_key = f"{log.get('model_provider')}:{log.get('model_name')}"
                models_used.add(model_key)
            
            if len(models_used) > 1:
                multi_model_sessions[session_id] = {
                    'log_count': len(logs),
                    'models': list(models_used),
                    'analysis_types': list(set(log.get('analysis_type') for log in logs)),
                    'images': list(set(log.get('image_id') for log in logs if log.get('image_id'))),
                    'time_span': (
                        max(log['created_at'] for log in logs) if logs[0].get('created_at') else None,
                        min(log['created_at'] for log in logs) if logs[0].get('created_at') else None
                    )
                }
    
    return multi_model_sessions


def analyze_cost_tracking(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze token and cost tracking"""
    cost_stats = {
        'total_logs': len(logs),
        'logs_with_tokens': 0,
        'logs_with_input_output_tokens': 0,
        'logs_with_cost': 0,
        'total_estimated_cost': 0,
        'cost_by_model': defaultdict(lambda: {'count': 0, 'total_cost': 0, 'avg_tokens': 0})
    }
    
    for log in logs:
        if log.get('tokens_used') is not None:
            cost_stats['logs_with_tokens'] += 1
        
        if log.get('input_tokens') is not None and log.get('output_tokens') is not None:
            cost_stats['logs_with_input_output_tokens'] += 1
        
        if log.get('estimated_cost') is not None:
            cost_stats['logs_with_cost'] += 1
            cost_stats['total_estimated_cost'] += float(log['estimated_cost'])
            
            model_key = f"{log.get('model_provider')}:{log.get('model_name')}"
            cost_stats['cost_by_model'][model_key]['count'] += 1
            cost_stats['cost_by_model'][model_key]['total_cost'] += float(log['estimated_cost'])
            if log.get('tokens_used'):
                cost_stats['cost_by_model'][model_key]['avg_tokens'] += log['tokens_used']
    
    # Calculate averages
    for model_data in cost_stats['cost_by_model'].values():
        if model_data['count'] > 0:
            model_data['avg_cost'] = model_data['total_cost'] / model_data['count']
            model_data['avg_tokens'] = model_data['avg_tokens'] / model_data['count']
    
    return cost_stats


def analyze_prompt_and_response_storage(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze prompt and response storage patterns"""
    storage_stats = {
        'total_logs': len(logs),
        'logs_with_prompt': 0,
        'logs_with_raw_response': 0,
        'logs_with_parsed_response': 0,
        'avg_prompt_length': 0,
        'avg_response_length': 0,
        'custom_prompts': 0,
        'template_prompts': 0
    }
    
    prompt_lengths = []
    response_lengths = []
    
    for log in logs:
        if log.get('prompt_text'):
            storage_stats['logs_with_prompt'] += 1
            prompt_lengths.append(len(log['prompt_text']))
            
            if log.get('custom_prompt'):
                storage_stats['custom_prompts'] += 1
            else:
                storage_stats['template_prompts'] += 1
        
        if log.get('raw_response'):
            storage_stats['logs_with_raw_response'] += 1
            response_lengths.append(len(log['raw_response']))
        
        if log.get('parsed_response'):
            storage_stats['logs_with_parsed_response'] += 1
    
    if prompt_lengths:
        storage_stats['avg_prompt_length'] = sum(prompt_lengths) / len(prompt_lengths)
    
    if response_lengths:
        storage_stats['avg_response_length'] = sum(response_lengths) / len(response_lengths)
    
    return storage_stats


def generate_report(logs: List[Dict[str, Any]], sessions: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate comprehensive audit report"""
    report = []
    report.append("=" * 80)
    report.append("AI ANALYSIS LOGS AUDIT REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")
    
    # 1. Basic Statistics
    report.append("1. BASIC STATISTICS")
    report.append("-" * 40)
    report.append(f"Total records analyzed: {len(logs)}")
    report.append(f"Date range: {logs[-1]['created_at'] if logs else 'N/A'} to {logs[0]['created_at'] if logs else 'N/A'}")
    report.append("")
    
    # 2. Field Completeness Analysis
    report.append("2. FIELD COMPLETENESS ANALYSIS")
    report.append("-" * 40)
    field_stats = analyze_field_completeness(logs)
    
    # Create table for field analysis
    field_data = []
    for field, stats in sorted(field_stats.items()):
        field_data.append([
            field,
            f"{stats['populated']}/{len(logs)}",
            f"{stats['percentage_populated']:.1f}%",
            str(stats['sample_values'][:1])[1:-1] if stats['sample_values'] else "N/A"
        ])
    
    # Simple table format
    report.append(f"{'Field':<30} {'Populated':<12} {'%':<8} {'Sample Value'}")
    report.append("-" * 80)
    for row in field_data:
        report.append(f"{row[0]:<30} {row[1]:<12} {row[2]:<8} {row[3]}")
    report.append("")
    
    # 3. Multi-Model Analysis Patterns
    report.append("3. MULTI-MODEL ANALYSIS PATTERNS")
    report.append("-" * 40)
    multi_model_sessions = analyze_multi_model_patterns(sessions)
    
    if multi_model_sessions:
        report.append(f"Found {len(multi_model_sessions)} multi-model sessions:")
        for session_id, data in list(multi_model_sessions.items())[:5]:  # Show first 5
            report.append(f"\n  Session: {session_id}")
            report.append(f"  - Models used: {', '.join(data['models'])}")
            report.append(f"  - Number of analyses: {data['log_count']}")
            report.append(f"  - Analysis types: {', '.join(data['analysis_types'])}")
            report.append(f"  - Images analyzed: {len(data['images'])}")
    else:
        report.append("No multi-model sessions found in recent data")
    report.append("")
    
    # 4. Cost and Token Tracking
    report.append("4. COST AND TOKEN TRACKING")
    report.append("-" * 40)
    cost_stats = analyze_cost_tracking(logs)
    
    report.append(f"Logs with token data: {cost_stats['logs_with_tokens']}/{cost_stats['total_logs']} ({cost_stats['logs_with_tokens']/cost_stats['total_logs']*100:.1f}%)")
    report.append(f"Logs with input/output tokens: {cost_stats['logs_with_input_output_tokens']}/{cost_stats['total_logs']} ({cost_stats['logs_with_input_output_tokens']/cost_stats['total_logs']*100:.1f}%)")
    report.append(f"Logs with cost data: {cost_stats['logs_with_cost']}/{cost_stats['total_logs']} ({cost_stats['logs_with_cost']/cost_stats['total_logs']*100:.1f}%)")
    report.append(f"Total estimated cost: ${cost_stats['total_estimated_cost']:.6f}")
    
    if cost_stats['cost_by_model']:
        report.append("\nCost breakdown by model:")
        cost_data = []
        for model, stats in cost_stats['cost_by_model'].items():
            if stats['count'] > 0:
                cost_data.append([
                    model,
                    stats['count'],
                    f"${stats['total_cost']:.6f}",
                    f"${stats.get('avg_cost', 0):.6f}",
                    f"{stats.get('avg_tokens', 0):.0f}"
                ])
        # Simple table format
        report.append(f"{'Model':<40} {'Count':<8} {'Total Cost':<12} {'Avg Cost':<12} {'Avg Tokens'}")
        report.append("-" * 80)
        for row in cost_data:
            report.append(f"{row[0]:<40} {row[1]:<8} {row[2]:<12} {row[3]:<12} {row[4]}")
    report.append("")
    
    # 5. Prompt and Response Storage
    report.append("5. PROMPT AND RESPONSE STORAGE")
    report.append("-" * 40)
    storage_stats = analyze_prompt_and_response_storage(logs)
    
    report.append(f"Logs with prompt_text: {storage_stats['logs_with_prompt']}/{storage_stats['total_logs']} ({storage_stats['logs_with_prompt']/storage_stats['total_logs']*100:.1f}%)")
    report.append(f"  - Custom prompts: {storage_stats['custom_prompts']}")
    report.append(f"  - Template prompts: {storage_stats['template_prompts']}")
    report.append(f"  - Average prompt length: {storage_stats['avg_prompt_length']:.0f} characters")
    report.append(f"\nLogs with raw_response: {storage_stats['logs_with_raw_response']}/{storage_stats['total_logs']} ({storage_stats['logs_with_raw_response']/storage_stats['total_logs']*100:.1f}%)")
    report.append(f"  - Average response length: {storage_stats['avg_response_length']:.0f} characters")
    report.append(f"\nLogs with parsed_response: {storage_stats['logs_with_parsed_response']}/{storage_stats['total_logs']} ({storage_stats['logs_with_parsed_response']/storage_stats['total_logs']*100:.1f}%)")
    report.append("")
    
    # 6. Key Findings Summary
    report.append("6. KEY FINDINGS SUMMARY")
    report.append("-" * 40)
    
    # Check for one record per model
    if multi_model_sessions:
        report.append("✓ Multi-model analyses ARE being tracked with session_id")
        report.append(f"  - Found {len(multi_model_sessions)} sessions with multiple models")
        avg_models_per_session = sum(len(s['models']) for s in multi_model_sessions.values()) / len(multi_model_sessions)
        report.append(f"  - Average models per multi-model session: {avg_models_per_session:.1f}")
    else:
        report.append("✗ No multi-model sessions found in recent data")
    
    # Check image_id storage
    image_id_populated = field_stats.get('image_id', {}).get('percentage_populated', 0)
    if image_id_populated > 95:
        report.append(f"✓ image_id is being saved ({image_id_populated:.1f}% populated)")
    else:
        report.append(f"✗ image_id is NOT consistently saved ({image_id_populated:.1f}% populated)")
    
    # Check prompt storage
    if storage_stats['logs_with_prompt'] == storage_stats['total_logs']:
        report.append("✓ Exact prompt_text is being saved for all analyses")
    else:
        report.append(f"✗ prompt_text is missing for {storage_stats['total_logs'] - storage_stats['logs_with_prompt']} records")
    
    # Check token/cost tracking
    if cost_stats['logs_with_tokens'] > cost_stats['total_logs'] * 0.9:
        report.append("✓ Tokens are being tracked consistently")
    else:
        report.append(f"✗ Token tracking is incomplete ({cost_stats['logs_with_tokens']}/{cost_stats['total_logs']})")
    
    if cost_stats['logs_with_cost'] > cost_stats['total_logs'] * 0.9:
        report.append("✓ Costs are being calculated and saved")
    else:
        report.append(f"✗ Cost tracking is incomplete ({cost_stats['logs_with_cost']}/{cost_stats['total_logs']})")
    
    # Check response storage
    if storage_stats['logs_with_raw_response'] == storage_stats['total_logs']:
        report.append("✓ Raw responses are being saved for all analyses")
    else:
        report.append(f"✗ Raw responses are missing for {storage_stats['total_logs'] - storage_stats['logs_with_raw_response']} records")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """Main execution function"""
    print("Fetching recent ai_analysis_logs...")
    
    # Fetch recent logs
    logs = fetch_recent_logs(limit=100)  # Get more for better analysis
    
    if not logs:
        print("No logs found in ai_analysis_logs table")
        return
    
    print(f"Fetched {len(logs)} records")
    
    # Fetch logs grouped by session
    print("Fetching logs by session_id...")
    sessions = fetch_logs_by_session()
    print(f"Found {len(sessions)} sessions with session_id")
    
    # Generate report
    report = generate_report(logs, sessions)
    
    # Print report
    print("\n" + report)
    
    # Save report to file
    report_filename = f"ai_analysis_logs_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_filename}")


if __name__ == "__main__":
    main()