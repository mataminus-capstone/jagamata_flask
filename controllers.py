from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User, Article, bcrypt
from datetime import datetime
from chatbot_model import chatbot

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
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registrasi berhasil! Silakan login.', 'success')
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
            login_user(user)
            flash(f'Selamat datang {user.username}!', 'success')
            return redirect(url_for('home.index'))
        
        flash('Username atau password salah!', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

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
