from flask import Blueprint, request, jsonify
from controllers.auth_controller import AuthController

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    return AuthController.register()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    return AuthController.login()

@auth_bp.route('/verify-email/<token>', methods=['GET', 'POST'])
def verify_email(token):
    """Verify user email with token"""
    return AuthController.verify_email(token)

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    return AuthController.forgot_password()

@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Reset password with token"""
    return AuthController.reset_password(token)

@auth_bp.route('/oauth/google', methods=['GET'])
def oauth_login():
    """Initiate Google OAuth login"""
    return AuthController.oauth_login()

@auth_bp.route('/oauth/callback', methods=['GET'])
def oauth_callback():
    """Handle Google OAuth callback"""
    return AuthController.oauth_callback()

@auth_bp.route('/oauth/mobile/callback', methods=['POST'])
def oauth_mobile_callback():
    """Handle Google OAuth callback for mobile apps
    
    Mobile apps call this endpoint with the authorization code to exchange for JWT token
    Request body: { "code": "auth_code_from_google" }
    """
    return AuthController.oauth_mobile_callback()

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info (requires auth token)"""
    return AuthController.get_current_user()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    return AuthController.logout()
