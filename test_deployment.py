#!/usr/bin/env python3
"""
Test Script um zu prüfen ob alle Dependencies verfügbar sind
"""

def test_imports():
    """Teste alle neuen Imports"""
    try:
        print("Testing imports...")
        
        # Test pywebpush
        from pywebpush import webpush, WebPushException
        print("✅ pywebpush import successful")
        
        # Test cryptography
        from cryptography.hazmat.primitives.asymmetric import ec
        print("✅ cryptography import successful")
        
        # Test VAPID Service
        from backend.services.vapid_service import VAPIDService
        print("✅ VAPIDService import successful")
        
        # Test Push Subscription Model
        from backend.models.push_subscription import PushSubscription
        print("✅ PushSubscription model import successful")
        
        # Test Push Notification Service
        from backend.services.push_notifications import PushNotificationService
        print("✅ PushNotificationService import successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_vapid_keys():
    """Teste VAPID-Keys"""
    try:
        from backend.services.vapid_service import VAPIDService
        
        print("\nTesting VAPID keys...")
        
        # Test public key
        public_key = VAPIDService.get_vapid_public_key()
        print(f"✅ Public key: {public_key[:50]}...")
        
        # Test private key
        private_key = VAPIDService.get_vapid_private_key()
        print(f"✅ Private key: {private_key[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ VAPID key error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Gourmen PWA Deployment...")
    
    imports_ok = test_imports()
    vapid_ok = test_vapid_keys()
    
    if imports_ok and vapid_ok:
        print("\n✅ All tests passed! Deployment should work.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
