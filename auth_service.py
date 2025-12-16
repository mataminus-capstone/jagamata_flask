import os
import requests
from datetime import datetime, timedelta
from flask import current_app
from models import db, User
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlencode

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


class EmailService:
    
    def __init__(self, app=None):
        self.smtp_host = None
        self.smtp_port = None
        self.sender_email = None
        self.sender_name = None
        self.api_key = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.smtp_host = app.config['BREVO_SMTP_HOST']
        self.smtp_port = app.config['BREVO_SMTP_PORT']
        self.sender_email = app.config['BREVO_SENDER_EMAIL']
        self.sender_name = app.config['BREVO_SENDER_NAME']
        self.api_key = app.config['BREVO_API_KEY']
    
    def send_email(self, to_email, subject, html_content):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.api_key)
                server.send_message(msg)
            
            return True
        except Exception as e:
            current_app.logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_verification_email(self, user, verification_url):
        """Send email verification"""
        subject = "Verifikasi Email Anda"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Verifikasi Email Anda</h2>
                <p>Halo {user.username},</p>
                <p>Terima kasih telah mendaftar! Silakan klik tombol di bawah untuk memverifikasi email Anda:</p>
                <a href="{verification_url}" class="button">Verifikasi Email</a>
                <p>Atau salin dan tempel link berikut di browser Anda:</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <div class="footer">
                    <p>Jika Anda tidak mendaftar akun ini, abaikan email ini.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self.send_email(user.email, subject, html_content)
    
    def send_password_reset_email(self, user, reset_url):
        """Send password reset email"""
        subject = "Reset Password Anda"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Reset Password</h2>
                <p>Halo {user.username},</p>
                <p>Kami menerima permintaan untuk reset password Anda. Klik tombol di bawah untuk reset password:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p>Atau salin dan tempel link berikut di browser Anda:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p><strong>Link ini akan kadaluarsa dalam 1 jam.</strong></p>
                <div class="footer">
                    <p>Jika Anda tidak meminta reset password, abaikan email ini.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self.send_email(user.email, subject, html_content)
    
    def send_welcome_email(self, user):
        """Send welcome email after verification"""
        subject = "Selamat Datang!"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Selamat Datang, {user.username}!</h2>
                <p>Email Anda telah berhasil diverifikasi.</p>
                <p>Anda sekarang dapat menikmati semua fitur aplikasi kami.</p>
                <div class="footer">
                    <p>Terima kasih telah bergabung dengan kami!</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self.send_email(user.email, subject, html_content)


# Initialize services
google_oauth = GoogleOAuth()
email_service = EmailService()
