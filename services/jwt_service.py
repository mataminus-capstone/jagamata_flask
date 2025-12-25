"""JWT token service for authentication"""
import jwt
import os
from datetime import datetime, timedelta
from flask import current_app

class JWTService:
    """Service for JWT token generation and validation"""
    
    @staticmethod
    def generate_token(user_id, user_role=None, expires_in_hours=24):
        """Generate JWT token for user"""
        try:
            secret_key = current_app.config.get('SECRET_KEY', os.getenv('SECRET_KEY', 'your-secret-key-change-this'))
            
            payload = {
                'user_id': user_id,
                'role': user_role,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
            }
            
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            return token
        except Exception as e:
            current_app.logger.error(f"Error generating JWT token: {str(e)}")
            return None
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token and return payload"""
        try:
            secret_key = current_app.config.get('SECRET_KEY', os.getenv('SECRET_KEY', 'your-secret-key-change-this'))
            
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            current_app.logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            current_app.logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            current_app.logger.error(f"Error verifying JWT token: {str(e)}")
            return None
    
    @staticmethod
    def extract_token_from_headers(headers):
        """Extract JWT token from Authorization header"""
        auth_header = headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        return token
