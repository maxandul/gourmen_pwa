"""
VAPID Service für Web Push Notifications
Generiert und verwaltet VAPID-Keys für echte Push-Benachrichtigungen
"""

import base64
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import os

class VAPIDService:
    """Service für VAPID (Voluntary Application Server Identification) Keys"""
    
    @staticmethod
    def generate_vapid_keys():
        """Generiert ein neues VAPID-Key-Paar"""
        # Generiere ECDSA P-256 private key
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Serialisiere private key
        private_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
        
        # Hole public key
        public_key = private_key.public_key()
        
        # Konvertiere public key zu uncompressed point format
        public_numbers = public_key.public_numbers()
        
        # P-256 public key ist 65 bytes (0x04 + 32 bytes x + 32 bytes y)
        x_bytes = public_numbers.x.to_bytes(32, 'big')
        y_bytes = public_numbers.y.to_bytes(32, 'big')
        public_point = b'\x04' + x_bytes + y_bytes
        
        # Base64 URL-safe encode
        public_key_b64 = base64.urlsafe_b64encode(public_point).decode('utf-8').rstrip('=')
        
        return {
            'private_key': private_pem.decode('utf-8'),
            'public_key': public_key_b64
        }
    
    @staticmethod
    def get_vapid_public_key():
        """Holt den öffentlichen VAPID-Key für den Client"""
        try:
            # 1. Prüfe zuerst Umgebungsvariablen (PRIMÄR für Production)
            public_key = os.environ.get('VAPID_PUBLIC_KEY')
            if public_key:
                return public_key.strip()
            
            # 2. Prüfe ob in Production (NICHT automatisch generieren!)
            is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION')
            if is_production:
                raise Exception(
                    "VAPID_PUBLIC_KEY environment variable not set! "
                    "Push notifications cannot work without valid VAPID keys. "
                    "Set VAPID_PUBLIC_KEY in Railway dashboard."
                )
            
            # 3. Development: Prüfe ob bereits Keys in Dateien existieren
            public_key_file = os.path.join(os.path.dirname(__file__), '..', '..', 'vapid_public.txt')
            
            if os.path.exists(public_key_file):
                with open(public_key_file, 'r') as f:
                    return f.read().strip()
            
            # 4. Development: Generiere neue Keys
            print("⚠️  No VAPID keys found. Generating new keys for development...")
            keys = VAPIDService.generate_vapid_keys()
            
            # Speichere Keys für Development
            private_key_file = os.path.join(os.path.dirname(__file__), '..', '..', 'vapid_private.pem')
            
            with open(private_key_file, 'w') as f:
                f.write(keys['private_key'])
            
            with open(public_key_file, 'w') as f:
                f.write(keys['public_key'])
            
            print(f"✓ VAPID keys saved to:")
            print(f"  - {public_key_file}")
            print(f"  - {private_key_file}")
            print(f"\n📋 Public Key: {keys['public_key']}")
            print(f"\n⚠️  For production, set these as environment variables in Railway!")
            
            return keys['public_key']
            
        except Exception as e:
            raise Exception(f"VAPID public key not available: {e}")
    
    @staticmethod
    def get_vapid_private_key():
        """Holt den privaten VAPID-Key für den Server"""
        try:
            # 1. Prüfe zuerst Umgebungsvariablen (PRIMÄR für Production)
            private_key = os.environ.get('VAPID_PRIVATE_KEY')
            if private_key:
                # Normalize escaped newlines (Railway/Heroku style)
                if '\\n' in private_key and '-----BEGIN' in private_key:
                    private_key = private_key.replace('\\n', '\n')
                return private_key.strip()
            
            # 2. Prüfe ob in Production (NICHT automatisch generieren!)
            is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION')
            if is_production:
                raise Exception(
                    "VAPID_PRIVATE_KEY environment variable not set! "
                    "Push notifications cannot work without valid VAPID keys. "
                    "Set VAPID_PRIVATE_KEY in Railway dashboard."
                )
            
            # 3. Development: Prüfe ob bereits Keys in Dateien existieren
            private_key_file = os.path.join(os.path.dirname(__file__), '..', '..', 'vapid_private.pem')
            
            if os.path.exists(private_key_file):
                with open(private_key_file, 'r') as f:
                    return f.read().strip()
            
            # 4. Development: Generiere Keys (ruft get_vapid_public_key auf)
            VAPIDService.get_vapid_public_key()  # Generiert beide Keys
            
            # Lies den generierten private key
            with open(private_key_file, 'r') as f:
                return f.read().strip()
                
        except Exception as e:
            raise Exception(f"VAPID private key not available: {e}")
