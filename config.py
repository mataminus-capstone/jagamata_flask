import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Web OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
    
    # Mobile OAuth (Android & iOS)
    GOOGLE_MOBILE_CLIENT_ID = os.getenv('GOOGLE_MOBILE_CLIENT_ID')
    
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    RESEND_SENDER_EMAIL = os.getenv('RESEND_SENDER_EMAIL')
    RESEND_SENDER_NAME = os.getenv('RESEND_SENDER_NAME', 'Jagamata')
    
    JWT_EXPIRATION_HOURS = os.getenv('JWT_EXPIRATION_HOURS', 24)
    

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
