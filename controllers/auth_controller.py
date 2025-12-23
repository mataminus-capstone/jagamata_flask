from flask import request, jsonify, current_app, redirect
from models import db, User
from services.auth_service import google_oauth, email_service
from datetime import datetime

class AuthController:
    
    @staticmethod
    def register():
        """Register a new user"""
        try:
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            
            # Validation
            if not username or not email or not password:
                return jsonify({
                    'success': False,
                    'message': 'Username, email, dan password harus diisi!'
                }), 400
            
            if len(password) < 6:
                return jsonify({
                    'success': False,
                    'message': 'Password minimal 6 karakter!'
                }), 400
            
            if User.query.filter_by(username=username).first():
                return jsonify({
                    'success': False,
                    'message': 'Username sudah terdaftar!'
                }), 400
            
            if User.query.filter_by(email=email).first():
                return jsonify({
                    'success': False,
                    'message': 'Email sudah terdaftar!'
                }), 400
            
            # Create user
            user = User(username=username, email=email, role='user')
            user.set_password(password)
            
            # Generate verification token
            token = user.generate_verification_token()
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email (optional, don't fail if email fails)
            try:
                verification_url = f"{request.host_url}api/auth/verify-email/{token}"
                email_service.send_verification_email(user, verification_url)
            except Exception as e:
                current_app.logger.warning(f"Email verification failed: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Registrasi berhasil! Silakan cek email untuk verifikasi.',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'email_verified': user.email_verified
                }
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"Register error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat registrasi.'
            }), 500
    
    @staticmethod
    def login():
        """Login user"""
        try:
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                return jsonify({
                    'success': False,
                    'message': 'Username dan password harus diisi!'
                }), 400
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                # TODO: VERIVIED SMTP
                # if not user.email_verified:
                #     return jsonify({
                #         'success': False,
                #         'message': 'Email belum diverifikasi. Silakan cek email Anda untuk link verifikasi.',
                #         'data': {
                #             'user_id': user.id,
                #             'email': user.email,
                #             'needs_verification': True
                #         }
                #     }), 403
                
                return jsonify({
                    'success': True,
                    'message': f'Login berhasil! Selamat datang {user.username}',
                    'data': {
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'email_verified': user.email_verified,
                        'created_at': user.created_at.isoformat()
                    }
                }), 200
            
            return jsonify({
                'success': False,
                'message': 'Username atau password salah!'
            }), 401
            
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat login.'
            }), 500
    
    @staticmethod
    def verify_email(token):
        """Verify user email"""
        try:
            user = User.query.filter_by(verification_token=token).first()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Token verifikasi tidak valid atau sudah kadaluarsa!'
                }), 400
            
            user.email_verified = True
            user.verification_token = None
            db.session.commit()
            
            # Send welcome email
            try:
                email_service.send_welcome_email(user)
            except Exception as e:
                current_app.logger.warning(f"Welcome email failed: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Email berhasil diverifikasi!',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email_verified': user.email_verified
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Verify email error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat verifikasi email.'
            }), 500
    
    @staticmethod
    def forgot_password():
        """Handle forgot password request"""
        try:
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            email = data.get('email', '').strip()
            
            if not email:
                return jsonify({
                    'success': False,
                    'message': 'Email harus diisi!'
                }), 400
            
            user = User.query.filter_by(email=email).first()
            
            if user and not user.oauth_provider:
                # Generate reset token
                token = user.generate_reset_token()
                db.session.commit()
                
                # Send reset email
                try:
                    reset_url = f"{request.host_url}api/auth/reset-password/{token}"
                    email_service.send_password_reset_email(user, reset_url)
                except Exception as e:
                    current_app.logger.warning(f"Reset email failed: {str(e)}")
            
            # Always return success to prevent email enumeration
            return jsonify({
                'success': True,
                'message': 'Jika email terdaftar, link reset password telah dikirim.'
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Forgot password error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat memproses permintaan.'
            }), 500
    
    @staticmethod
    def reset_password(token):
        """Reset password with token"""
        try:
            user = User.query.filter_by(reset_token=token).first()
            
            if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
                return jsonify({
                    'success': False,
                    'message': 'Token reset tidak valid atau sudah kadaluarsa!'
                }), 400
            
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            password = data.get('password', '').strip()
            confirm_password = data.get('confirm_password', '').strip()
            
            if not password or not confirm_password:
                return jsonify({
                    'success': False,
                    'message': 'Password dan konfirmasi password harus diisi!'
                }), 400
            
            if len(password) < 6:
                return jsonify({
                    'success': False,
                    'message': 'Password minimal 6 karakter!'
                }), 400
            
            if password != confirm_password:
                return jsonify({
                    'success': False,
                    'message': 'Password tidak cocok!'
                }), 400
            
            # Reset password
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Password berhasil direset! Silakan login.'
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Reset password error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat reset password.'
            }), 500
    
    @staticmethod
    def oauth_login():
        """Initiate OAuth login with Google"""
        try:
            oauth_url = google_oauth.get_google_oauth_url()
            
            if oauth_url:
                return jsonify({
                    'success': True,
                    'data': {
                        'oauth_url': oauth_url
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Gagal menginisialisasi OAuth.'
                }), 500
                
        except Exception as e:
            current_app.logger.error(f"OAuth login error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat OAuth login.'
            }), 500
    
    @staticmethod
    def oauth_callback():
        """Handle OAuth callback from Google"""
        try:
            code = request.args.get('code')
            error = request.args.get('error')
            
            if error:
                return jsonify({
                    'success': False,
                    'message': f'OAuth gagal: {error}'
                }), 400
            
            if not code:
                return jsonify({
                    'success': False,
                    'message': 'Kode otorisasi tidak ditemukan.'
                }), 400
            
            # Exchange code for token
            token_data = google_oauth.exchange_code_for_token(code)
            
            if not token_data or 'access_token' not in token_data:
                return jsonify({
                    'success': False,
                    'message': 'Gagal mendapatkan access token.'
                }), 400
            
            # Get user info
            user_data = google_oauth.get_user_info(token_data['access_token'])
            
            if not user_data:
                return jsonify({
                    'success': False,
                    'message': 'Gagal memverifikasi OAuth.'
                }), 400
            
            # Get or create user
            oauth_id = user_data.get('id')
            email = user_data.get('email')
            
            user = User.query.filter_by(oauth_id=oauth_id).first()
            
            if not user:
                user = User.query.filter_by(email=email).first()
                if user:
                    # Link existing account with OAuth
                    user.oauth_provider = 'google'
                    user.oauth_id = oauth_id
                    user.email_verified = True
                else:
                    # Create new user
                    username = email.split('@')[0]
                    # Ensure unique username
                    base_username = username
                    counter = 1
                    while User.query.filter_by(username=username).first():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    user = User(
                        username=username,
                        email=email,
                        oauth_provider='google',
                        oauth_id=oauth_id,
                        email_verified=True,
                        role='user'
                    )
                    db.session.add(user)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Login berhasil! Selamat datang {user.username}',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'email_verified': user.email_verified,
                    'oauth_provider': user.oauth_provider
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"OAuth callback error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat OAuth callback.'
            }), 500
    
    @staticmethod
    def get_current_user():
        """Get current user info (requires auth token in future)"""
        # TODO: Implement JWT token validation
        return jsonify({
            'success': False,
            'message': 'Not implemented yet. Requires JWT authentication.'
        }), 501
    
    @staticmethod
    def logout():
        """Logout user"""
        # For stateless API, client should just remove the token
        return jsonify({
            'success': True,
            'message': 'Logout berhasil!'
        }), 200
