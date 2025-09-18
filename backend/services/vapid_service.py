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
            # Prüfe zuerst Umgebungsvariablen (für Produktion)
            public_key = os.environ.get('VAPID_PUBLIC_KEY')
            if public_key:
                return public_key
            
            # Fallback: Prüfe ob bereits Keys existieren
            private_key_file = os.path.join(os.path.dirname(__file__), '..', '..', 'vapid_private.pem')
            public_key_file = os.path.join(os.path.dirname(__file__), '..', '..', 'vapid_public.txt')
            
            if os.path.exists(public_key_file):
                with open(public_key_file, 'r') as f:
                    return f.read().strip()
            
            # Generiere neue Keys (nur für Development)
            keys = VAPIDService.generate_vapid_keys()
            
            # Speichere Keys nur in Development
            with open(private_key_file, 'w') as f:
                f.write(keys['private_key'])
            
            with open(public_key_file, 'w') as f:
                f.write(keys['public_key'])
            
            return keys['public_key']
            
        except Exception as e:
            raise Exception(f"VAPID public key not available: {e}")
    
    @staticmethod
    def get_vapid_private_key():
        """Holt den privaten VAPID-Key für den Server"""
        try:
            # Prüfe zuerst Umgebungsvariablen (für Produktion)
            private_key = os.environ.get('VAPID_PRIVATE_KEY')
            if private_key:
                # Normalize escaped newlines (Railway/Heroku style)
                if '\\n' in private_key and '-----BEGIN' in private_key:
                    private_key = private_key.replace('\\n', '\n')
                return private_key
            
            # Fallback: Prüfe ob bereits Keys existieren
            private_key_file = os.path.join(os.path.dirname(__file__), '..', '..', 'vapid_private.pem')
            
            if os.path.exists(private_key_file):
                with open(private_key_file, 'r') as f:
                    return f.read().strip()
            
            # Falls keine Keys existieren, generiere sie (nur für Development)
            VAPIDService.get_vapid_public_key()  # Das generiert auch den private key
            
            with open(private_key_file, 'r') as f:
                return f.read().strip()
                
        except Exception as e:
            raise Exception(f"VAPID private key not available: {e}")
