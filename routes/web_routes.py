from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Article
from functools import wraps
from services.auth_service import email_service

web_bp = Blueprint('web', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    return decorated_function

@web_bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('web.dashboard'))
        return redirect(url_for('web.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.email_verified:
                flash('Email belum diverifikasi. Silakan cek email Anda untuk link verifikasi.', 'error')
                return render_template('login.html')
            
            login_user(user)
            flash('Login successful!', 'success')
            if user.is_admin():
                return redirect(url_for('web.dashboard'))
            return redirect(url_for('web.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for('web.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()  # save to get user.id
        
        # Generate verification token & send email
        from services.auth_service import email_service
        token = user.generate_verification_token()
        db.session.commit()
        
        try:
            verification_url = f"{request.host_url}api/auth/verify-email/{token}"
            email_service.send_verification_email(user, verification_url)
        except Exception as e:
            current_app.logger.warning(f"Email verification failed: {str(e)}")
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('web.login'))
    
    return render_template('register.html')

@web_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('web.index'))

@web_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    
    stats = {
        'total_articles': Article.query.count(),
        'total_users': User.query.count(),
        'user_articles': Article.query.filter_by(author_id=current_user.id).count(),
        'verified_count': User.query.filter_by(email_verified=True).count(),
        'admin_count': User.query.filter_by(role='admin').count(),
        'moderator_count': User.query.filter_by(role='moderator').count(),
        'user_count': User.query.filter_by(role='user').count()
    }
    
    return render_template('dashboard.html', recent_articles=recent_articles, stats=stats)

@web_bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    """Manage users page"""
    return render_template('manage_users.html')


@web_bp.route('/dashboard/articles', methods=['GET'])
@login_required
@admin_required
def dashboard_articles():
    """Admin dashboard articles management page"""
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('manage_articles.html', articles=articles)

@web_bp.route('/dashboard/articles/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_article():
    """Create article page (admin only)"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        article = Article(title=title, content=content, author_id=current_user.id)
        db.session.add(article)
        db.session.commit()
        
        flash('Article created successfully!', 'success')
        return redirect(url_for('web.article_detail', article_id=article.id))
    
    return render_template('create.html')

@web_bp.route('/dashboard/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_article(article_id):
    """Edit article page (admin and author only)"""
    article = Article.query.get_or_404(article_id)
    
    if article.author_id != current_user.id:
        flash('You can only edit your own articles', 'error')
        return redirect(url_for('web.article_detail', article_id=article_id))
    
    if request.method == 'POST':
        article.title = request.form.get('title')
        article.content = request.form.get('content')
        db.session.commit()
        
        flash('Article updated successfully!', 'success')
        return redirect(url_for('web.article_detail', article_id=article_id))
    
    return render_template('edit.html', article=article)

@web_bp.route('/dashboard/articles/<int:article_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_article(article_id):
    """Delete article (admin and author only)"""
    article = Article.query.get_or_404(article_id)
    
    if article.author_id != current_user.id:
        flash('You can only delete your own articles', 'error')
        return redirect(url_for('web.article_detail', article_id=article_id))
    
    db.session.delete(article)
    db.session.commit()
    
    flash('Article deleted successfully!', 'success')
    return redirect(url_for('web.dashboard_articles'))


@web_bp.route('/articles')
def articles():
    """Browse all articles page (public - for all users)"""
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('articles_public.html', articles=articles)

@web_bp.route('/article/<int:article_id>')
def article_detail(article_id):
    """Article detail page (public - read only for all users)"""
    article = Article.query.get_or_404(article_id)
    return render_template('detail.html', article=article)

@web_bp.route('/chatbot', methods=['POST'])
def chatbot_web():
    """Chatbot endpoint for web UI"""
    from services.chatbot_service import chatbot
    
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return {'success': False, 'response': 'Please provide a message'}, 400
    
    response = chatbot.get_response(message)
    return {'success': True, 'response': response}, 200

@web_bp.route('/forgot-password')
def forgot_password():
    """Forgot password page"""
    return render_template('forgot_password.html')

@web_bp.route('/oauth/google')
def oauth_google():
    """Initiate Google OAuth for web UI"""
    from services.auth_service import google_oauth
    try:
        oauth_url = google_oauth.get_google_oauth_url()
        if oauth_url:
            return redirect(oauth_url)
        else:
            flash('Failed to initialize Google OAuth', 'error')
            return redirect(url_for('web.login'))
    except Exception as e:
        flash('OAuth error occurred', 'error')
        return redirect(url_for('web.login'))

@web_bp.route('/oauth/callback')
def oauth_callback():
    """Handle Google OAuth callback for web UI"""
    print("CALLBACK HIT", request.url)
    from services.auth_service import google_oauth
    
    try:
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            flash(f'OAuth failed: {error}', 'error')
            return redirect(url_for('web.login'))
        
        if not code:
            flash('Authorization code not found', 'error')
            return redirect(url_for('web.login'))
        
        # Exchange code for token
        token_data = google_oauth.exchange_code_for_token(code)
        
        if not token_data or 'access_token' not in token_data:
            flash('Failed to get access token', 'error')
            return redirect(url_for('web.login'))
        
        # Get user info
        user_data = google_oauth.get_user_info(token_data['access_token'])
        
        if not user_data:
            flash('Failed to verify OAuth', 'error')
            return redirect(url_for('web.login'))
        
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
        
        # Login user with Flask-Login
        login_user(user)
        flash(f'Login successful! Welcome {user.username}', 'success')
        
        if user.is_admin():
            return redirect(url_for('web.dashboard'))
        return redirect(url_for('web.index'))
        
    except Exception as e:
        flash('OAuth error occurred', 'error')
        return redirect(url_for('web.login'))
