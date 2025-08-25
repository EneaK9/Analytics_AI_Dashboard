#!/usr/bin/env python3
"""
Direct test of JWT token verification to debug 403 errors
"""
import sys
import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import verify_token, create_access_token
    import jwt
    
    print("🔑 Testing JWT token creation and verification...")
    
    # Test data
    test_email = "peelz@gmail.com"
    test_client_id = "3b619a14-3cd8-49fa-9c24-d8df5e54c452"
    
    # Create a test token
    test_data = {
        "email": test_email,
        "client_id": test_client_id
    }
    
    print(f"📝 Creating token for: {test_email}")
    token = create_access_token(test_data)
    print(f"✅ Token created: {token[:50]}...")
    
    # Try to verify the token
    print(f"🔍 Verifying token...")
    try:
        result = verify_token(token)
        print(f"✅ Token verification SUCCESS!")
        print(f"   - Client ID: {result.client_id}")
        print(f"   - Email: {result.email}")
    except Exception as e:
        print(f"❌ Token verification FAILED: {e}")
        print(f"   - Error type: {type(e).__name__}")
        traceback.print_exc()
    
    # Check the raw JWT payload
    print(f"\n🔍 Raw JWT analysis:")
    try:
        # Decode without verification first to see payload
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"   - Raw payload: {payload}")
        
        # Try to decode with verification
        from app import JWT_SECRET_KEY, JWT_ALGORITHM
        verified_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print(f"   - Verified payload: {verified_payload}")
        
    except Exception as e:
        print(f"   - JWT decode error: {e}")
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Import or setup error: {e}")
    traceback.print_exc()
