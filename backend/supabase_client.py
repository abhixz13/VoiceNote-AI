"""
Supabase client configuration for Python backend
"""

import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """
    Get configured Supabase client with proxy settings disabled
    
    Returns:
        Supabase client instance
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    
    # Temporarily remove proxy environment variables to avoid conflicts
    # Railway sets HTTP_PROXY/HTTPS_PROXY which causes issues with Supabase client
    old_http_proxy = os.environ.pop('HTTP_PROXY', None)
    old_https_proxy = os.environ.pop('HTTPS_PROXY', None)
    old_http_proxy_lower = os.environ.pop('http_proxy', None)
    old_https_proxy_lower = os.environ.pop('https_proxy', None)
    
    try:
        client = create_client(supabase_url, supabase_key)
    finally:
        # Restore proxy settings if they existed
        if old_http_proxy:
            os.environ['HTTP_PROXY'] = old_http_proxy
        if old_https_proxy:
            os.environ['HTTPS_PROXY'] = old_https_proxy
        if old_http_proxy_lower:
            os.environ['http_proxy'] = old_http_proxy_lower
        if old_https_proxy_lower:
            os.environ['https_proxy'] = old_https_proxy_lower
    
    return client
