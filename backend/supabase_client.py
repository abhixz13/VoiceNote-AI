"""
Supabase client configuration for Python backend
"""

import os

# Clear ALL proxy environment variables BEFORE importing supabase
# Railway sets these which cause conflicts with httpx/httpcore used by Supabase
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']:
    os.environ.pop(proxy_var, None)

from supabase import create_client, Client

def get_supabase_client() -> Client:
    """
    Get configured Supabase client (proxy variables already cleared at module import)
    
    Returns:
        Supabase client instance
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    
    return create_client(supabase_url, supabase_key)
