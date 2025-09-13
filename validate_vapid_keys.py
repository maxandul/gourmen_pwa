#!/usr/bin/env python3
"""
Validiert VAPID-Keys in Railway Environment
"""

import os
import sys
import base64

def validate_vapid_keys():
    """Validiert VAPID-Keys aus Environment Variables"""
    print("=== VAPID KEYS VALIDATION ===")
    
    # Hole Keys aus Environment
    public_key = os.environ.get('VAPID_PUBLIC_KEY')
    private_key = os.environ.get('VAPID_PRIVATE_KEY')
    
    if not public_key:
        print("❌ VAPID_PUBLIC_KEY not set in environment")
        return False
    
    if not private_key:
        print("❌ VAPID_PRIVATE_KEY not set in environment")
        return False
    
    print(f"✓ VAPID_PUBLIC_KEY found: {public_key[:20]}...")
    print(f"✓ VAPID_PRIVATE_KEY found: {private_key[:50]}...")
    
    # Validiere Public Key Format
    try:
        # Public Key sollte Base64 URL-safe sein
        if len(public_key) < 40:
            print("❌ VAPID_PUBLIC_KEY too short")
            return False
        
        # Teste Base64 Decoding
        decoded = base64.urlsafe_b64decode(public_key + '==')
        if len(decoded) != 65:  # P-256 public key sollte 65 bytes sein
            print(f"❌ VAPID_PUBLIC_KEY wrong length: {len(decoded)} bytes (expected 65)")
            return False
        
        print("✓ VAPID_PUBLIC_KEY format valid")
        
    except Exception as e:
        print(f"❌ VAPID_PUBLIC_KEY format invalid: {e}")
        return False
    
    # Validiere Private Key Format
    try:
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ VAPID_PRIVATE_KEY missing PEM header")
            return False
        
        if not private_key.endswith('-----END PRIVATE KEY-----'):
            print("❌ VAPID_PRIVATE_KEY missing PEM footer")
            return False
        
        print("✓ VAPID_PRIVATE_KEY format valid")
        
    except Exception as e:
        print(f"❌ VAPID_PRIVATE_KEY format invalid: {e}")
        return False
    
    # Teste ob Keys zusammenpassen
    try:
        sys.path.insert(0, '/app/backend')
        from backend.services.vapid_service import VAPIDService
        
        # Teste ob Service die Keys laden kann
        test_public = VAPIDService.get_vapid_public_key()
        test_private = VAPIDService.get_vapid_private_key()
        
        if test_public == public_key:
            print("✓ VAPID_PUBLIC_KEY matches service")
        else:
            print("❌ VAPID_PUBLIC_KEY doesn't match service")
            return False
        
        if test_private == private_key:
            print("✓ VAPID_PRIVATE_KEY matches service")
        else:
            print("❌ VAPID_PRIVATE_KEY doesn't match service")
            return False
        
        print("✅ All VAPID keys are valid!")
        return True
        
    except Exception as e:
        print(f"❌ VAPID service test failed: {e}")
        return False

if __name__ == '__main__':
    success = validate_vapid_keys()
    sys.exit(0 if success else 1)
