import os
import requests
from datetime import datetime, timedelta
from flask import current_app
from models import db, User
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlencode
from services.jwt_service import JWTService


class GoogleOAuth:
    
    def __init__(self, app=None):
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.client_id = app.config['GOOGLE_CLIENT_ID']
        self.client_secret = app.config['GOOGLE_CLIENT_SECRET']
        self.redirect_uri = app.config['GOOGLE_REDIRECT_URI']
    
    def get_google_oauth_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        print("OAUTH URL:", oauth_url)
        return oauth_url
    
    def exchange_code_for_token(self, code):
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Token exchange failed: {response.text}")
                return None
        except Exception as e:
            current_app.logger.error(f"Error exchanging code for token: {str(e)}")
            return None
    
    def get_user_info(self, access_token):
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(userinfo_url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Get user info failed: {response.text}")
                return None
        except Exception as e:
            current_app.logger.error(f"Error getting user info: {str(e)}")
            return None


class ResendEmailService:
    """
    Email service using Resend API.
    Resend is a modern email API with excellent deliverability.
    """
    
    def __init__(self, app=None):
        self.api_key = None
        self.sender_email = None
        self.sender_name = None
        self.base_url = "https://api.resend.com"
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app config"""
        self.api_key = app.config.get('RESEND_API_KEY')
        self.sender_email = app.config.get('RESEND_SENDER_EMAIL')
        self.sender_name = app.config.get('RESEND_SENDER_NAME', 'Jagamata')
        
        if not self.api_key:
            current_app.logger.warning("RESEND_API_KEY not configured")
    
    def _make_request(self, method, endpoint, data=None):
        """
        Helper method to make requests to Resend API
        
        Args:
            method: HTTP method (POST, GET, etc.)
            endpoint: API endpoint (e.g., 'emails')
            data: Request payload
        
        Returns:
            Response JSON or None if request fails
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                response = requests.request(method, url, json=data, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                current_app.logger.error(
                    f"Resend API error ({response.status_code}): {response.text}"
                )
                return None
                
        except Exception as e:
            current_app.logger.error(f"Error calling Resend API: {str(e)}")
            return None
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """
        Send email using Resend API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
        
        Returns:
            Boolean indicating success
        """
        payload = {
            "from": f"{self.sender_name} <{self.sender_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        if text_content:
            payload["text"] = text_content
        
        result = self._make_request("POST", "emails", payload)
        
        if result and result.get("id"):
            current_app.logger.info(f"Email sent successfully to {to_email} (ID: {result['id']})")
            return True
        else:
            current_app.logger.error(f"Failed to send email to {to_email}")
            return False
    
    def send_verification_email(self, user, verification_url):
        """Send email verification with beautiful design"""
        subject = "Verifikasi Email Anda - Jagamata"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="id">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 20px auto; 
                    background: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px 20px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    font-size: 28px;
                    margin-bottom: 10px;
                    font-weight: 600;
                }}
                .header p {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 16px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .greeting strong {{
                    color: #667eea;
                }}
                .message {{
                    font-size: 15px;
                    line-height: 1.8;
                    color: #555;
                    margin: 20px 0;
                }}
                .button-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 14px 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                }}
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
                }}
                .link-section {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .link-section p {{
                    font-size: 13px;
                    color: #666;
                    margin-bottom: 10px;
                }}
                .link-section a {{
                    color: #667eea;
                    text-decoration: none;
                    word-break: break-all;
                    font-size: 12px;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 25px 30px;
                    border-top: 1px solid #eee;
                    text-align: center;
                }}
                .footer p {{
                    font-size: 13px;
                    color: #999;
                    line-height: 1.6;
                }}
                .footer-divider {{
                    margin: 15px 0;
                    color: #ddd;
                }}
                .security-badge {{
                    display: inline-block;
                    padding: 8px 12px;
                    background: #e8f0fe;
                    color: #1967d2;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✓ Verifikasi Email Anda</h1>
                    <p>Langkah penting untuk mengamankan akun Anda</p>
                </div>
                
                <div class="content">
                    <p class="greeting">Halo <strong>{user.username}</strong>,</p>
                    
                    <p class="message">
                        Terima kasih telah mendaftar di Jagamata! Kami senang memiliki Anda sebagai bagian dari komunitas kami.
                    </p>
                    
                    <p class="message">
                        Untuk menyelesaikan pendaftaran dan mengakses semua fitur, silakan verifikasi email Anda dengan mengklik tombol di bawah:
                    </p>
                    
                    <div class="button-container">
                        <a href="{verification_url}" class="button">Verifikasi Email Saya</a>
                    </div>
                    
                    <p class="message" style="text-align: center; color: #999; font-size: 14px;">
                        Atau jika tombol di atas tidak berfungsi, gunakan link berikut:
                    </p>
                    
                    <div class="link-section">
                        <a href="{verification_url}">{verification_url}</a>
                    </div>
                    
                    <p class="message" style="color: #999; font-size: 13px;">
                        Link verifikasi ini akan berlaku selama <strong>24 jam</strong>.
                    </p>
                </div>
                
                <div class="footer">
                    <p>
                        ℹ️ Jika Anda tidak membuat akun ini, Anda dapat mengabaikan email ini dengan aman.
                    </p>
                    <p class="footer-divider">—</p>
                    <p>
                        <strong>Jagamata</strong><br>
                        Layanan Inovatif untuk Kesehatan Mata<br>
                        <a href="#" style="color: #667eea; text-decoration: none;">www.jagamata.com</a>
                    </p>
                    <div class="security-badge">🔒 Email terenkripsi dan aman</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Verifikasi Email Anda - Jagamata
        
        Halo {user.username},
        
        Terima kasih telah mendaftar di Jagamata!
        
        Untuk menyelesaikan pendaftaran, silakan kunjungi link berikut:
        {verification_url}
        
        Link ini berlaku selama 24 jam.
        
        Jika Anda tidak membuat akun ini, abaikan email ini.
        
        Jagamata
        """
        
        return self.send_email(user.email, subject, html_content, text_content)
    
    def send_password_reset_email(self, user, reset_url):
        """Send password reset email with beautiful design"""
        subject = "Reset Password Anda - Jagamata"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="id">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    color: #333;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    min-height: 100vh;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 20px auto; 
                    background: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 40px 20px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    font-size: 28px;
                    margin-bottom: 10px;
                    font-weight: 600;
                }}
                .header p {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .alert {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                    font-size: 14px;
                    color: #856404;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 16px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .greeting strong {{
                    color: #f5576c;
                }}
                .message {{
                    font-size: 15px;
                    line-height: 1.8;
                    color: #555;
                    margin: 20px 0;
                }}
                .button-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 14px 40px;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
                }}
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(245, 87, 108, 0.6);
                }}
                .link-section {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .link-section p {{
                    font-size: 13px;
                    color: #666;
                    margin-bottom: 10px;
                }}
                .link-section a {{
                    color: #f5576c;
                    text-decoration: none;
                    word-break: break-all;
                    font-size: 12px;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 25px 30px;
                    border-top: 1px solid #eee;
                    text-align: center;
                }}
                .footer p {{
                    font-size: 13px;
                    color: #999;
                    line-height: 1.6;
                }}
                .footer-divider {{
                    margin: 15px 0;
                    color: #ddd;
                }}
                .security-badge {{
                    display: inline-block;
                    padding: 8px 12px;
                    background: #e8f0fe;
                    color: #1967d2;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Reset Password</h1>
                    <p>Perbarui password Anda dengan aman</p>
                </div>
                
                <div class="content">
                    <p class="greeting">Halo <strong>{user.username}</strong>,</p>
                    
                    <div class="alert">
                        ⚠️ Kami menerima permintaan untuk mereset password akun Anda. Jika Anda tidak memintanya, abaikan email ini.
                    </div>
                    
                    <p class="message">
                        Untuk reset password Anda, silakan klik tombol di bawah:
                    </p>
                    
                    <div class="button-container">
                        <a href="{reset_url}" class="button">Reset Password Saya</a>
                    </div>
                    
                    <p class="message" style="text-align: center; color: #999; font-size: 14px;">
                        Atau jika tombol di atas tidak berfungsi, gunakan link berikut:
                    </p>
                    
                    <div class="link-section">
                        <a href="{reset_url}">{reset_url}</a>
                    </div>
                    
                    <p class="message" style="color: #999; font-size: 13px;">
                        ⏱️ Link reset password ini hanya berlaku selama <strong>1 jam</strong> untuk keamanan Anda.
                    </p>
                </div>
                
                <div class="footer">
                    <p>
                        🔒 Jika Anda tidak meminta reset password, tidak ada tindakan yang diperlukan. Password Anda tetap aman.
                    </p>
                    <p class="footer-divider">—</p>
                    <p>
                        <strong>Jagamata</strong><br>
                        Layanan Inovatif untuk Kesehatan Mata<br>
                        <a href="#" style="color: #f5576c; text-decoration: none;">www.jagamata.com</a>
                    </p>
                    <div class="security-badge">🔐 Email terenkripsi dan aman</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Password Anda - Jagamata
        
        Halo {user.username},
        
        Kami menerima permintaan untuk reset password Anda.
        
        Untuk reset password, kunjungi link berikut:
        {reset_url}
        
        Link ini berlaku selama 1 jam.
        
        Jika Anda tidak meminta reset password, abaikan email ini.
        
        Jagamata
        """
        
        return self.send_email(user.email, subject, html_content, text_content)
    
    def send_welcome_email(self, user):
        """Send welcome email after verification"""
        subject = "Selamat Datang di Jagamata! 🎉"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="id">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    color: #333;
                    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    min-height: 100vh;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 20px auto; 
                    background: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    padding: 50px 20px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    font-size: 32px;
                    margin-bottom: 10px;
                    font-weight: 700;
                }}
                .header p {{
                    font-size: 16px;
                    opacity: 0.95;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .greeting strong {{
                    color: #38f9d7;
                }}
                .features {{
                    margin: 30px 0;
                }}
                .feature-item {{
                    display: flex;
                    align-items: flex-start;
                    margin: 15px 0;
                    padding: 15px;
                    background: #f0fdf9;
                    border-radius: 8px;
                    border-left: 4px solid #38f9d7;
                }}
                .feature-icon {{
                    font-size: 24px;
                    margin-right: 15px;
                    flex-shrink: 0;
                }}
                .feature-text {{
                    font-size: 15px;
                    line-height: 1.6;
                    color: #555;
                }}
                .feature-text strong {{
                    color: #333;
                    display: block;
                    margin-bottom: 5px;
                }}
                .button-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 14px 40px;
                    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    box-shadow: 0 4px 15px rgba(67, 233, 123, 0.4);
                }}
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(67, 233, 123, 0.6);
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 25px 30px;
                    border-top: 1px solid #eee;
                    text-align: center;
                }}
                .footer p {{
                    font-size: 13px;
                    color: #999;
                    line-height: 1.6;
                }}
                .footer-divider {{
                    margin: 15px 0;
                    color: #ddd;
                }}
                .social-links {{
                    margin: 15px 0;
                }}
                .social-links a {{
                    display: inline-block;
                    margin: 0 10px;
                    color: #38f9d7;
                    text-decoration: none;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Selamat Datang!</h1>
                    <p>Email Anda telah diverifikasi dengan sukses</p>
                </div>
                
                <div class="content">
                    <p class="greeting">Halo <strong>{user.username}</strong>,</p>
                    
                    <p style="font-size: 15px; line-height: 1.8; color: #555; margin: 20px 0;">
                        Akun Anda sudah siap digunakan! Anda sekarang memiliki akses penuh ke semua fitur Jagamata. Kami sangat senang memiliki Anda sebagai bagian dari komunitas kami.
                    </p>
                    
                    <div class="features">
                        <div class="feature-item">
                            <div class="feature-icon">💬</div>
                            <div class="feature-text">
                                <strong>Chat dengan AI</strong>
                                Dapatkan dukungan kesehatan mata 24/7 dari asisten AI kami yang cerdas.
                            </div>
                        </div>
                        
                        <div class="feature-item">
                            <div class="feature-icon">📚</div>
                            <div class="feature-text">
                                <strong>Artikel & Panduan</strong>
                                Akses ke ribuan artikel informatif tentang kesehatan mata.
                            </div>
                        </div>
                        
                        <div class="feature-item">
                            <div class="feature-icon">🎯</div>
                            <div class="feature-text">
                                <strong>Rencana Personal</strong>
                                Buat rencana kesehatan mata yang disesuaikan dengan kebutuhan Anda.
                            </div>
                        </div>
                    </div>
                    
                    <div class="button-container">
                        <a href="https://jagamata.com" class="button">Mulai Sekarang</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>
                        Jika Anda memiliki pertanyaan, jangan ragu untuk menghubungi kami.
                    </p>
                    <p class="footer-divider">—</p>
                    <p>
                        <strong>Jagamata</strong><br>
                        Layanan Inovatif untuk Kesehatan Mata<br>
                        <a href="#" style="color: #38f9d7; text-decoration: none;">www.jagamata.com</a>
                    </p>
                    <div class="social-links">
                        <a href="#">Instagram</a> • <a href="#">Twitter</a> • <a href="#">Facebook</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Selamat Datang di Jagamata!
        
        Halo {user.username},
        
        Akun Anda sudah siap digunakan! Email Anda telah berhasil diverifikasi.
        
        Anda sekarang memiliki akses ke semua fitur Jagamata:
        - Chat dengan AI untuk dukungan kesehatan mata
        - Akses ke ribuan artikel informatif
        - Buat rencana kesehatan mata personal
        
        Mulai sekarang: https://jagamata.com
        
        Terima kasih telah bergabung dengan kami!
        
        Jagamata
        """
        
        return self.send_email(user.email, subject, html_content, text_content)


# Initialize services
google_oauth = GoogleOAuth()
email_service = ResendEmailService()
jwt_service = JWTService()
