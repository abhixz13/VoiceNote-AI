#!/usr/bin/env python3
"""
Test script to verify Supabase client fix
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("❌ No .env file found")
        sys.exit(1)
except ImportError:
    print("❌ python-dotenv not available")
    sys.exit(1)

def test_supabase_connection():
    """Test Supabase client connection"""
    try:
        # Check if required environment variables are set
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            return False
        
        print("✅ Environment variables are set")
        
        # Test Supabase connection
        print("🔄 Testing Supabase client initialization...")
        from supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        print("✅ Supabase client initialized successfully!")
        
        # Test a simple query
        print("🔄 Testing database connection...")
        response = supabase.table('recordings').select('recording_id').limit(1).execute()
        print(f"✅ Database query successful. Found {len(response.data)} recordings")
        
        if response.data:
            print(f"📝 Sample recording ID: {response.data[0]['recording_id']}")
        else:
            print("📝 No recordings found in database")
        
        # Test storage connection
        print("🔄 Testing storage connection...")
        try:
            buckets = supabase.storage.list_buckets()
            print(f"✅ Storage connection successful. Found {len(buckets)} buckets")
            for bucket in buckets:
                print(f"   📁 Bucket: {bucket.name}")
        except Exception as e:
            print(f"⚠️  Storage test failed (this might be normal): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Supabase Integration Fix")
    print("=" * 50)
    
    success = test_supabase_connection()
    
    print("=" * 50)
    if success:
        print("🎉 Supabase integration is working!")
        print("✅ Ready to run transcription service")
    else:
        print("❌ Supabase integration still has issues")
        print("🔧 May need additional troubleshooting")
