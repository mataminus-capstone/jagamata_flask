from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User, Article, bcrypt
from datetime import datetime
from chatbot_model import chatbot
from auth_service import google_oauth, email_service

def register_controller():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Password minimal 6 karakter!', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Password tidak cocok!', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username sudah terdaftar!', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, email=email, role='user')
        user.set_password(password)
        
        token = user.generate_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        if email_service.send_verification_email(user, verification_url):
            flash('Registrasi berhasil! Silakan cek email Anda untuk verifikasi.', 'success')
        else:
            flash('Registrasi berhasil, tetapi gagal mengirim email verifikasi. Silakan hubungi admin.', 'warning')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

def login_controller():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username dan password harus diisi!', 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.email_verified and not user.oauth_provider:
                flash('Silakan verifikasi email Anda terlebih dahulu!', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user)
            flash(f'Selamat datang {user.username}!', 'success')
            return redirect(url_for('home.index'))
        
        flash('Username atau password salah!', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

def oauth_login_controller():
    """Initiate OAuth login with Google"""
    oauth_url = google_oauth.get_google_oauth_url()
    
    if oauth_url:
        return redirect(oauth_url)
    else:
        flash('Gagal menginisialisasi OAuth. Silakan coba lagi.', 'danger')
        return redirect(url_for('auth.login'))

def oauth_callback_controller():
    """Handle OAuth callback from Google"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f'OAuth gagal: {error}', 'danger')
        return redirect(url_for('auth.login'))
    
    if not code:
        flash('OAuth gagal. Kode otorisasi tidak ditemukan.', 'danger')
        return redirect(url_for('auth.login'))
    
    token_data = google_oauth.exchange_code_for_token(code)
    
    if not token_data or 'access_token' not in token_data:
        flash('Gagal mendapatkan access token. Silakan coba lagi.', 'danger')
        return redirect(url_for('auth.login'))
    
    user_data = google_oauth.get_user_info(token_data['access_token'])
    
    if not user_data:
        flash('Gagal memverifikasi OAuth. Silakan coba lagi.', 'danger')
        return redirect(url_for('auth.login'))
    
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
    login_user(user)
    flash(f'Selamat datang {user.username}!', 'success')
    return redirect(url_for('home.index'))

def verify_email_controller(token):
    """Verify user email"""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Token verifikasi tidak valid!', 'danger')
        return redirect(url_for('auth.login'))
    
    user.email_verified = True
    user.verification_token = None
    db.session.commit()
    
    # Send welcome email
    email_service.send_welcome_email(user)
    
    flash('Email berhasil diverifikasi! Silakan login.', 'success')
    return redirect(url_for('auth.login'))

def forgot_password_controller():
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email harus diisi!', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and not user.oauth_provider:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # Send reset email
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            if email_service.send_password_reset_email(user, reset_url):
                flash('Email reset password telah dikirim. Silakan cek inbox Anda.', 'success')
            else:
                flash('Gagal mengirim email. Silakan coba lagi.', 'danger')
        else:
            # Always show success to prevent email enumeration
            flash('Jika email terdaftar, link reset password telah dikirim.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

def reset_password_controller(token):
    """Handle password reset"""
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Token reset tidak valid atau sudah kadaluarsa!', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if len(password) < 6:
            flash('Password minimal 6 karakter!', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if password != confirm_password:
            flash('Password tidak cocok!', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Password berhasil direset! Silakan login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

def logout_controller():
    logout_user()
    flash('Anda telah logout!', 'success')
    return redirect(url_for('auth.login'))

def home_controller():
    stats = {
        'total_articles': Article.query.count(),
        'total_users': User.query.count(),
    }
    return render_template('index.html', stats=stats)

def articles_controller():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('articles.html', articles=articles)

def admin_dashboard_controller():
    if not current_user.is_admin():
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('home.index'))
    
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=10)
    
    stats = {
        'total_articles': Article.query.count(),
        'total_users': User.query.count(),
        'user_articles': Article.query.filter_by(author_id=current_user.id).count()
    }
    
    return render_template('admin/dashboard.html', articles=articles, stats=stats)

def article_detail_controller(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article/detail.html', article=article)

def create_article_controller():
    if not current_user.is_admin():
        flash('Hanya admin yang bisa membuat konten!', 'danger')
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Judul dan konten harus diisi!', 'danger')
            return redirect(url_for('article.create'))
        
        article = Article(title=title, content=content, author_id=current_user.id)
        db.session.add(article)
        db.session.commit()
        
        flash('Konten berhasil dibuat!', 'success')
        return redirect(url_for('article.detail', article_id=article.id))
    
    return render_template('article/create.html')

def edit_article_controller(article_id):
    article = Article.query.get_or_404(article_id)
    
    if not current_user.is_admin() or article.author_id != current_user.id:
        flash('Anda tidak punya akses untuk edit konten ini!', 'danger')
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Judul dan konten harus diisi!', 'danger')
            return redirect(url_for('article.edit', article_id=article.id))
        
        article.title = title
        article.content = content
        article.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Konten berhasil diupdate!', 'success')
        return redirect(url_for('article.detail', article_id=article.id))
    
    return render_template('article/edit.html', article=article)

def delete_article_controller(article_id):
    article = Article.query.get_or_404(article_id)
    
    if not current_user.is_admin() or article.author_id != current_user.id:
        flash('Anda tidak punya akses untuk hapus konten ini!', 'danger')
        return redirect(url_for('home.index'))
    
    db.session.delete(article)
    db.session.commit()
    
    flash('Konten berhasil dihapus!', 'success')
    return redirect(url_for('article.articles'))

def chatbot_controller():
    if request.method == 'POST':
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            
            if not message:
                return jsonify({
                    'response': 'Pesan tidak boleh kosong.',
                    'doctor': 'System',
                    'confidence': 0
                }), 400
            
            result = chatbot.predict(message)
            
            if 'error' in result:
                return jsonify({
                    'response': result['response'],
                    'doctor': 'System',
                    'confidence': 0
                }), 500
            
            return jsonify({
                'response': result['response'],
                'doctor': result['doctor'],
                'confidence': result['confidence']
            })
            
        except Exception as e:
            current_app.logger.error(f"Chatbot error: {str(e)}")
            return jsonify({
                'response': 'Terjadi kesalahan saat memproses pesan.',
                'doctor': 'System',
                'confidence': 0
            }), 500
    
    return jsonify({
        'status': 'ready' if chatbot.is_loaded else 'not_loaded',
        'message': 'Chatbot endpoint aktif' if chatbot.is_loaded else 'Model belum dimuat'
    })
