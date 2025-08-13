"""HAR file processing utilities for RetroRecon."""

import json
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional


def parse_har_file(content: bytes) -> List[Dict[str, Any]]:
    """Parse HAR file content and extract entries for database insertion."""
    try:
        content_str = content.decode('utf-8')
        har_data = json.loads(content_str)
        return extract_har_entries(har_data)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid HAR file format: {e}")


def extract_har_entries(har_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract entries from HAR data structure."""
    if 'log' not in har_data:
        raise ValueError("Invalid HAR format: missing 'log' section")
    
    log = har_data['log']
    if 'entries' not in log:
        raise ValueError("Invalid HAR format: missing 'entries' section")
    
    entries = []
    for entry in log['entries']:
        try:
            converted_entry = convert_har_entry(entry)
            if converted_entry:
                entries.append(converted_entry)
        except Exception as e:
            # Log but don't fail entire import for one bad entry
            print(f"Warning: Skipping invalid HAR entry: {e}")
            continue
    
    return entries


def convert_har_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a single HAR entry to database format."""
    if 'request' not in entry:
        return None
    
    request = entry['request']
    response = entry.get('response', {})
    
    # Extract URL
    url = request.get('url', '').strip()
    if not url:
        return None
    
    # Parse domain from URL
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc or ''
    
    # Extract timestamp and convert to appropriate format
    timestamp = None
    if 'startedDateTime' in entry:
        try:
            # Convert ISO format to timestamp format similar to CDX
            dt = datetime.fromisoformat(entry['startedDateTime'].replace('Z', '+00:00'))
            timestamp = dt.strftime('%Y%m%d%H%M%S')
        except Exception:
            pass
    
    # Extract request method
    request_method = request.get('method', 'GET').upper()
    
    # Extract response data
    status_code = response.get('status')
    mime_type = None
    content_size = None
    
    if 'content' in response:
        content = response['content']
        mime_type = content.get('mimeType', '').split(';')[0]  # Remove charset info
        content_size = content.get('size')
    
    # Extract timing information
    response_time_ms = entry.get('time')
    if response_time_ms is not None:
        response_time_ms = int(response_time_ms)
    
    # Extract headers (convert to JSON strings for storage)
    request_headers = None
    response_headers = None
    
    if 'headers' in request:
        request_headers = json.dumps({
            header['name']: header['value'] 
            for header in request['headers']
        })
    
    if 'headers' in response:
        response_headers = json.dumps({
            header['name']: header['value'] 
            for header in response['headers']
        })
    
    return {
        'url': url,
        'domain': domain,
        'timestamp': timestamp,
        'status_code': status_code,
        'mime_type': mime_type,
        'tags': 'har-import',  # Tag all HAR imports
        'request_method': request_method,
        'response_time_ms': response_time_ms,
        'content_size': content_size,
        'request_headers': request_headers,
        'response_headers': response_headers,
        'source_type': 'har'
    }


def format_har_timestamp(iso_timestamp: str) -> Optional[str]:
    """Convert ISO timestamp from HAR to CDX-style timestamp."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y%m%d%H%M%S')
    except Exception:
        return None


def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc or ''
    except Exception:
        return ''


def validate_har_structure(har_data: Dict[str, Any]) -> bool:
    """Validate basic HAR file structure."""
    if not isinstance(har_data, dict):
        return False
    
    if 'log' not in har_data:
        return False
    
    log = har_data['log']
    if not isinstance(log, dict):
        return False
    
    if 'entries' not in log:
        return False
    
    entries = log['entries']
    if not isinstance(entries, list):
        return False
    
    return True