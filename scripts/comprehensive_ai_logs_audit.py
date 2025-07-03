#!/usr/bin/env python3
"""
Comprehensive audit of ai_analysis_logs table with more detailed queries
"""

import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    sys.exit(1)

supabase: Client = create_client(url, key)


def get_all_logs_count() -> int:
    """Get total count of all logs"""
    try:
        response = supabase.table('ai_analysis_logs').select("id", count='exact').execute()
        return response.count if response.count else 0
    except Exception as e:
        print(f"Error getting total count: {e}")
        return 0


def get_logs_by_date_range(days_back: int = 30) -> List[Dict[str, Any]]:
    """Get logs from the last N days"""
    try:
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        response = supabase.table('ai_analysis_logs').select("*").gte(
            'created_at', start_date
        ).order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching logs by date range: {e}")
        return []


def analyze_by_analysis_type(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze logs grouped by analysis_type"""
    by_type = defaultdict(lambda: {'count': 0, 'models': set(), 'sessions': set()})
    
    for log in logs:
        analysis_type = log.get('analysis_type', 'unknown')
        by_type[analysis_type]['count'] += 1
        by_type[analysis_type]['models'].add(f"{log.get('model_provider')}:{log.get('model_name')}")
        if log.get('session_id'):
            by_type[analysis_type]['sessions'].add(log['session_id'])
    
    # Convert sets to lists for JSON serialization
    for type_data in by_type.values():
        type_data['models'] = list(type_data['models'])
        type_data['sessions'] = list(type_data['sessions'])
        type_data['avg_logs_per_session'] = type_data['count'] / max(len(type_data['sessions']), 1)
    
    return dict(by_type)


def analyze_model_usage(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detailed analysis of model usage patterns"""
    model_stats = defaultdict(lambda: {
        'count': 0,
        'successful': 0,
        'failed': 0,
        'total_tokens': 0,
        'total_cost': 0,
        'avg_confidence': 0,
        'confidence_sum': 0,
        'with_input_output_tokens': 0,
        'processing_times': []
    })
    
    for log in logs:
        model_key = f"{log.get('model_provider')}:{log.get('model_name')}"
        stats = model_stats[model_key]
        
        stats['count'] += 1
        
        if log.get('analysis_successful'):
            stats['successful'] += 1
        else:
            stats['failed'] += 1
        
        if log.get('tokens_used'):
            stats['total_tokens'] += log['tokens_used']
        
        if log.get('estimated_cost'):
            stats['total_cost'] += float(log['estimated_cost'])
        
        if log.get('confidence') is not None:
            stats['confidence_sum'] += log['confidence']
        
        if log.get('input_tokens') is not None and log.get('output_tokens') is not None:
            stats['with_input_output_tokens'] += 1
        
        if log.get('processing_time_ms'):
            stats['processing_times'].append(log['processing_time_ms'])
    
    # Calculate averages
    for model, stats in model_stats.items():
        if stats['count'] > 0:
            stats['avg_confidence'] = stats['confidence_sum'] / stats['count']
            stats['avg_tokens'] = stats['total_tokens'] / stats['count']
            stats['avg_cost'] = stats['total_cost'] / stats['count']
            if stats['processing_times']:
                stats['avg_processing_time_ms'] = sum(stats['processing_times']) / len(stats['processing_times'])
                stats['min_processing_time_ms'] = min(stats['processing_times'])
                stats['max_processing_time_ms'] = max(stats['processing_times'])
        
        # Remove intermediate data
        del stats['confidence_sum']
        del stats['processing_times']
    
    return dict(model_stats)


def analyze_session_patterns(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze session patterns in detail"""
    sessions = defaultdict(list)
    
    # Group by session
    for log in logs:
        if log.get('session_id'):
            sessions[log['session_id']].append(log)
    
    session_stats = {
        'total_sessions': len(sessions),
        'single_model_sessions': 0,
        'multi_model_sessions': 0,
        'session_details': []
    }
    
    for session_id, session_logs in sessions.items():
        models = set(f"{log.get('model_provider')}:{log.get('model_name')}" for log in session_logs)
        
        if len(models) == 1:
            session_stats['single_model_sessions'] += 1
        else:
            session_stats['multi_model_sessions'] += 1
            
            # Add details for multi-model sessions
            session_detail = {
                'session_id': session_id,
                'log_count': len(session_logs),
                'models': list(models),
                'analysis_types': list(set(log.get('analysis_type') for log in session_logs)),
                'time_span_seconds': None,
                'all_successful': all(log.get('analysis_successful', False) for log in session_logs),
                'image_ids': list(set(log.get('image_id') for log in session_logs if log.get('image_id')))
            }
            
            # Calculate time span
            timestamps = [log.get('created_at') for log in session_logs if log.get('created_at')]
            if len(timestamps) >= 2:
                oldest = min(timestamps)
                newest = max(timestamps)
                # Parse timestamps and calculate difference
                try:
                    old_dt = datetime.fromisoformat(oldest.replace('Z', '+00:00'))
                    new_dt = datetime.fromisoformat(newest.replace('Z', '+00:00'))
                    session_detail['time_span_seconds'] = (new_dt - old_dt).total_seconds()
                except:
                    pass
            
            session_stats['session_details'].append(session_detail)
    
    # Sort by log count
    session_stats['session_details'].sort(key=lambda x: x['log_count'], reverse=True)
    
    return session_stats


def analyze_data_completeness(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze data completeness with more detail"""
    total = len(logs) if logs else 1  # Avoid division by zero
    
    completeness = {
        'total_records': len(logs),
        'critical_fields': {},
        'optional_fields': {},
        'token_tracking': {},
        'response_storage': {}
    }
    
    # Critical fields that should always be present
    critical_fields = [
        'image_id', 'analysis_type', 'prompt_text', 'model_provider', 
        'model_name', 'analysis_successful', 'created_at'
    ]
    
    # Optional but important fields
    optional_fields = [
        'camera_name', 'captured_at', 'confidence', 'processing_time_ms',
        'session_id', 'config_id', 'task_id', 'error_message'
    ]
    
    # Count field presence
    for field in critical_fields:
        count = sum(1 for log in logs if log.get(field) is not None and log[field] != '')
        completeness['critical_fields'][field] = {
            'count': count,
            'percentage': (count / total) * 100
        }
    
    for field in optional_fields:
        count = sum(1 for log in logs if log.get(field) is not None and log[field] != '')
        completeness['optional_fields'][field] = {
            'count': count,
            'percentage': (count / total) * 100
        }
    
    # Token tracking analysis
    completeness['token_tracking'] = {
        'has_tokens_used': sum(1 for log in logs if log.get('tokens_used') is not None),
        'has_input_tokens': sum(1 for log in logs if log.get('input_tokens') is not None),
        'has_output_tokens': sum(1 for log in logs if log.get('output_tokens') is not None),
        'has_both_input_output': sum(1 for log in logs if 
            log.get('input_tokens') is not None and log.get('output_tokens') is not None),
        'has_estimated_cost': sum(1 for log in logs if log.get('estimated_cost') is not None)
    }
    
    # Response storage analysis
    completeness['response_storage'] = {
        'has_raw_response': sum(1 for log in logs if log.get('raw_response')),
        'has_parsed_response': sum(1 for log in logs if log.get('parsed_response')),
        'raw_response_empty': sum(1 for log in logs if log.get('raw_response') == ''),
        'avg_raw_response_length': 0,
        'custom_prompts': sum(1 for log in logs if log.get('custom_prompt') == True)
    }
    
    # Calculate average response length
    response_lengths = [len(log['raw_response']) for log in logs 
                       if log.get('raw_response') and log['raw_response'] != '']
    if response_lengths:
        completeness['response_storage']['avg_raw_response_length'] = sum(response_lengths) / len(response_lengths)
    
    return completeness


def generate_detailed_report(logs: List[Dict[str, Any]]) -> str:
    """Generate comprehensive report with all analyses"""
    report = []
    report.append("=" * 100)
    report.append("COMPREHENSIVE AI ANALYSIS LOGS AUDIT REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 100)
    report.append("")
    
    # Get total count
    total_count = get_all_logs_count()
    report.append(f"Total records in database: {total_count}")
    report.append(f"Records analyzed (last 30 days): {len(logs)}")
    
    if not logs:
        report.append("\nNO LOGS FOUND IN THE LAST 30 DAYS")
        return "\n".join(report)
    
    report.append("")
    
    # 1. Data Completeness
    report.append("1. DATA COMPLETENESS ANALYSIS")
    report.append("-" * 50)
    completeness = analyze_data_completeness(logs)
    
    report.append(f"Total records analyzed: {completeness['total_records']}")
    report.append("\nCritical Fields (should be 100%):")
    for field, data in completeness['critical_fields'].items():
        report.append(f"  {field:<20} {data['count']:>6}/{completeness['total_records']} ({data['percentage']:>5.1f}%)")
    
    report.append("\nOptional Fields:")
    for field, data in completeness['optional_fields'].items():
        report.append(f"  {field:<20} {data['count']:>6}/{completeness['total_records']} ({data['percentage']:>5.1f}%)")
    
    report.append("\nToken & Cost Tracking:")
    token_data = completeness['token_tracking']
    total = completeness['total_records']
    report.append(f"  Has tokens_used:     {token_data['has_tokens_used']:>6}/{total} ({token_data['has_tokens_used']/total*100:>5.1f}%)")
    report.append(f"  Has input_tokens:    {token_data['has_input_tokens']:>6}/{total} ({token_data['has_input_tokens']/total*100:>5.1f}%)")
    report.append(f"  Has output_tokens:   {token_data['has_output_tokens']:>6}/{total} ({token_data['has_output_tokens']/total*100:>5.1f}%)")
    report.append(f"  Has both I/O tokens: {token_data['has_both_input_output']:>6}/{total} ({token_data['has_both_input_output']/total*100:>5.1f}%)")
    report.append(f"  Has estimated_cost:  {token_data['has_estimated_cost']:>6}/{total} ({token_data['has_estimated_cost']/total*100:>5.1f}%)")
    
    report.append("\nResponse Storage:")
    response_data = completeness['response_storage']
    report.append(f"  Has raw_response:    {response_data['has_raw_response']:>6}/{total} ({response_data['has_raw_response']/total*100:>5.1f}%)")
    report.append(f"  Empty raw_response:  {response_data['raw_response_empty']:>6}")
    report.append(f"  Has parsed_response: {response_data['has_parsed_response']:>6}/{total} ({response_data['has_parsed_response']/total*100:>5.1f}%)")
    report.append(f"  Avg response length: {response_data['avg_raw_response_length']:>6.0f} chars")
    report.append(f"  Custom prompts:      {response_data['custom_prompts']:>6}/{total} ({response_data['custom_prompts']/total*100:>5.1f}%)")
    
    report.append("")
    
    # 2. Session Analysis
    report.append("2. SESSION ANALYSIS (Multi-Model Usage)")
    report.append("-" * 50)
    session_stats = analyze_session_patterns(logs)
    
    report.append(f"Total sessions with session_id: {session_stats['total_sessions']}")
    report.append(f"Single-model sessions: {session_stats['single_model_sessions']}")
    report.append(f"Multi-model sessions: {session_stats['multi_model_sessions']}")
    
    if session_stats['multi_model_sessions'] > 0:
        report.append("\nTop Multi-Model Sessions:")
        for i, session in enumerate(session_stats['session_details'][:10]):
            report.append(f"\n  Session {i+1}: {session['session_id']}")
            report.append(f"    Logs: {session['log_count']}")
            report.append(f"    Models: {', '.join(session['models'])}")
            report.append(f"    Analysis types: {', '.join(session['analysis_types'])}")
            report.append(f"    Images: {len(session['image_ids'])}")
            report.append(f"    Time span: {session['time_span_seconds']:.1f}s" if session['time_span_seconds'] else "    Time span: N/A")
            report.append(f"    All successful: {session['all_successful']}")
    
    report.append("")
    
    # 3. Model Usage Analysis
    report.append("3. MODEL USAGE ANALYSIS")
    report.append("-" * 50)
    model_stats = analyze_model_usage(logs)
    
    report.append(f"{'Model':<35} {'Count':>8} {'Success':>8} {'Failed':>8} {'Avg Tokens':>10} {'Avg Cost':>10} {'Avg Conf':>8}")
    report.append("-" * 100)
    
    for model, stats in sorted(model_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        report.append(f"{model:<35} {stats['count']:>8} {stats['successful']:>8} {stats['failed']:>8} "
                     f"{stats.get('avg_tokens', 0):>10.0f} ${stats.get('avg_cost', 0):>9.6f} "
                     f"{stats.get('avg_confidence', 0):>8.2f}")
    
    report.append("")
    
    # 4. Analysis Type Breakdown
    report.append("4. ANALYSIS TYPE BREAKDOWN")
    report.append("-" * 50)
    by_type = analyze_by_analysis_type(logs)
    
    for analysis_type, data in sorted(by_type.items(), key=lambda x: x[1]['count'], reverse=True):
        report.append(f"\n{analysis_type}:")
        report.append(f"  Total analyses: {data['count']}")
        report.append(f"  Unique sessions: {len(data['sessions'])}")
        report.append(f"  Avg logs per session: {data['avg_logs_per_session']:.1f}")
        report.append(f"  Models used: {', '.join(data['models'])}")
    
    report.append("")
    
    # 5. Key Findings Summary
    report.append("5. KEY FINDINGS SUMMARY")
    report.append("-" * 50)
    
    # One record per model?
    if session_stats['multi_model_sessions'] > 0:
        report.append("✓ Multi-model analyses ARE being tracked properly")
        report.append(f"  - {session_stats['multi_model_sessions']} multi-model sessions found")
        report.append(f"  - Sessions properly group related analyses using session_id")
    else:
        report.append("✗ No multi-model sessions found - may indicate:")
        report.append("  - Multi-model feature not being used")
        report.append("  - session_id not being properly set")
    
    # Image ID tracking
    image_id_pct = completeness['critical_fields']['image_id']['percentage']
    if image_id_pct > 95:
        report.append(f"✓ image_id is being saved consistently ({image_id_pct:.1f}%)")
    else:
        report.append(f"⚠ image_id tracking needs improvement ({image_id_pct:.1f}%)")
    
    # Prompt tracking
    prompt_pct = completeness['critical_fields']['prompt_text']['percentage']
    if prompt_pct > 95:
        report.append(f"✓ Exact prompts are being saved ({prompt_pct:.1f}%)")
    else:
        report.append(f"✗ Prompt tracking is incomplete ({prompt_pct:.1f}%)")
    
    # Token tracking
    token_pct = token_data['has_tokens_used'] / total * 100
    io_token_pct = token_data['has_both_input_output'] / total * 100
    if token_pct > 90:
        report.append(f"✓ Token tracking is good ({token_pct:.1f}%)")
        if io_token_pct < 50:
            report.append(f"  ⚠ But input/output token split is low ({io_token_pct:.1f}%)")
    else:
        report.append(f"✗ Token tracking needs improvement ({token_pct:.1f}%)")
    
    # Cost tracking
    cost_pct = token_data['has_estimated_cost'] / total * 100
    if cost_pct > 90:
        report.append(f"✓ Cost estimation is working ({cost_pct:.1f}%)")
    else:
        report.append(f"✗ Cost tracking is incomplete ({cost_pct:.1f}%)")
    
    # Response storage
    raw_pct = response_data['has_raw_response'] / total * 100
    if raw_pct > 95:
        report.append(f"✓ Raw responses are being saved ({raw_pct:.1f}%)")
        if response_data['raw_response_empty'] > 0:
            report.append(f"  ⚠ But {response_data['raw_response_empty']} responses are empty strings")
    else:
        report.append(f"✗ Raw response storage is incomplete ({raw_pct:.1f}%)")
    
    report.append("")
    report.append("=" * 100)
    
    return "\n".join(report)


def main():
    """Main execution function"""
    print("Performing comprehensive AI analysis logs audit...")
    print("Fetching logs from the last 30 days...")
    
    # Get logs from last 30 days
    logs = get_logs_by_date_range(30)
    
    # Generate comprehensive report
    report = generate_detailed_report(logs)
    
    # Print report
    print("\n" + report)
    
    # Save report
    filename = f"comprehensive_ai_logs_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {filename}")
    
    # Also create a JSON data dump for further analysis
    json_filename = f"ai_logs_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_filename, 'w') as f:
        json.dump({
            'audit_date': datetime.now().isoformat(),
            'total_records': len(logs),
            'logs_sample': logs[:10] if logs else [],  # First 10 records as sample
            'analysis_summary': {
                'completeness': analyze_data_completeness(logs),
                'session_patterns': analyze_session_patterns(logs),
                'model_usage': analyze_model_usage(logs),
                'by_analysis_type': analyze_by_analysis_type(logs)
            }
        }, f, indent=2, default=str)
    
    print(f"JSON data saved to: {json_filename}")


if __name__ == "__main__":
    main()