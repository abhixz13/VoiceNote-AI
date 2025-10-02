"""
Supabase client configuration for Python backend
"""

import os
import logging

# Clear ALL proxy environment variables BEFORE importing supabase
# Railway sets these which cause conflicts with httpx/httpcore used by Supabase
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']:
    os.environ.pop(proxy_var, None)

logger = logging.getLogger(__name__)

def get_supabase_client():
    """
    Get configured Supabase client with error handling for proxy issues
    
    Returns:
        Supabase client instance
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    
    try:
        # First attempt: Try with default configuration
        from supabase import create_client
        return create_client(supabase_url, supabase_key)
        
    except TypeError as e:
        if "unexpected keyword argument 'proxy'" in str(e):
            logger.warning("Proxy argument error detected, trying workaround...")
            
            # Workaround: Try with custom HTTP client configuration
            try:
                import httpx
                from supabase import create_client
                
                # Create a custom HTTP client without proxy configuration
                http_client = httpx.Client(
                    timeout=30.0,
                    follow_redirects=True
                )
                
                # Try to create client with custom options
                try:
                    from supabase.client import ClientOptions
                    options = ClientOptions()
                    return create_client(supabase_url, supabase_key, options)
                except Exception:
                    # If ClientOptions doesn't work, try direct approach
                    return create_client(supabase_url, supabase_key)
                    
            except Exception as inner_e:
                logger.error(f"Workaround failed: {inner_e}")
                raise RuntimeError(f"Failed to initialize Supabase client. Original error: {e}. Workaround error: {inner_e}")
        else:
            raise
            
    except Exception as e:
        logger.error(f"Unexpected error initializing Supabase client: {e}")
        raise
