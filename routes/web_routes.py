from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Article, Clinic, Category, Medicine
from functools import wraps
from services.auth_service import email_service
from services.jwt_service import JWTService
from services.cloudinary_service import CloudinaryService

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
            return redirect(url_for('web.index'))
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
            
            jwt_token = JWTService.generate_token(user.id, user.role)
            
            flash('Login berhasil!', 'success')
            if user.is_admin():
                return render_template('login_success.html', token=jwt_token, redirect_url=url_for('web.index'))
            return render_template('login_success.html', token=jwt_token, redirect_url=url_for('web.index'))
        else:
            flash('Email atau password salah', 'error')
    
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


def get_dashboard_stats():
    return {
        'total_articles': Article.query.count(),
        'total_users': User.query.count(),
        'total_clinics': Clinic.query.count(),
        'total_categories': Category.query.count(),
        'total_medicines': Medicine.query.count(),
        'user_articles': Article.query.filter_by(author_id=current_user.id).count(),
        'verified_count': User.query.filter_by(email_verified=True).count(),
        'admin_count': User.query.filter_by(role='admin').count(),
        'moderator_count': User.query.filter_by(role='moderator').count(),
        'user_count': User.query.filter_by(role='user').count()
    }

@web_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    stats = get_dashboard_stats()
    return render_template('dashboard.html', recent_articles=recent_articles, stats=stats)

@web_bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    """Manage users page"""
    return render_template('manage_users.html', stats=get_dashboard_stats())


@web_bp.route('/dashboard/articles', methods=['GET'])
@login_required
@admin_required
def dashboard_articles():
    """Admin dashboard articles management page"""
    page = request.args.get('page', 1, type=int)
    articles = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('manage_articles.html', articles=articles, stats=get_dashboard_stats())

@web_bp.route('/dashboard/clinics', methods=['GET'])
@login_required
@admin_required
def dashboard_clinics():
    """Admin dashboard clinics management page"""
    page = request.args.get('page', 1, type=int)
    clinics = Clinic.query.order_by(Clinic.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('manage_clinics.html', clinics=clinics, stats=get_dashboard_stats())

@web_bp.route('/dashboard/clinics/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_clinic():
    """Create clinic page (admin only)"""
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        
        # Handle Image Upload
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                upload_result = CloudinaryService.upload_image(file)
                if upload_result['success']:
                    image_url = upload_result['url']
                else:
                    flash(f'Gagal mengupload gambar: {upload_result.get("message")}', 'error')
                    return render_template('create_clinic.html')
        
        if not image_url:
             flash('Gambar klinik wajib diupload!', 'error')
             return render_template('create_clinic.html')

        clinic = Clinic(
            name=name, 
            address=address, 
            phone_number=phone_number,
            image_url=image_url
        )
        db.session.add(clinic)
        db.session.commit()
        
        flash('Klinik berhasil ditambahkan!', 'success')
        return redirect(url_for('web.dashboard_clinics'))
    
    return render_template('create_clinic.html')

@web_bp.route('/dashboard/clinics/<int:clinic_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_clinic(clinic_id):
    """Edit clinic page (admin only)"""
    clinic = Clinic.query.get_or_404(clinic_id)
    
    if request.method == 'POST':
        clinic.name = request.form.get('name')
        clinic.address = request.form.get('address')
        clinic.phone_number = request.form.get('phone_number')
        
        # Handle Image Upload (Optional)
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                upload_result = CloudinaryService.upload_image(file)
                if upload_result['success']:
                    clinic.image_url = upload_result['url']
                else:
                    flash(f'Gagal mengupload gambar: {upload_result.get("message")}', 'error')
                    return render_template('edit_clinic.html', clinic=clinic)
        
        db.session.commit()
        
        flash('Data klinik berhasil diperbarui!', 'success')
        return redirect(url_for('web.dashboard_clinics'))
    
    return render_template('edit_clinic.html', clinic=clinic)

@web_bp.route('/dashboard/clinics/<int:clinic_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_clinic(clinic_id):
    """Delete clinic (admin only)"""
    clinic = Clinic.query.get_or_404(clinic_id)
    
    db.session.delete(clinic)
    db.session.commit()
    
    flash('Klinik berhasil dihapus!', 'success')
    return redirect(url_for('web.dashboard_clinics'))

@web_bp.route('/dashboard/articles/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_article():
    """Create article page (admin only)"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Handle Image Upload
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                upload_result = CloudinaryService.upload_image(file)
                if upload_result['success']:
                    image_url = upload_result['url']
                else:
                    flash(f'Gagal mengupload gambar: {upload_result.get("message")}', 'error')
                    return render_template('create.html')
        
        article = Article(title=title, content=content, author_id=current_user.id, image_url=image_url)
        db.session.add(article)
        db.session.commit()
        
        flash('Article created successfully!', 'success')
        # Redirect to admin detail view instead of public
        return redirect(url_for('web.dashboard_article_detail', article_id=article.id))
    
    return render_template('create.html', stats=get_dashboard_stats())

@web_bp.route('/dashboard/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_article(article_id):
    """Edit article page (admin and author only)"""
    article = Article.query.get_or_404(article_id)
    
    # Author check removed for admins
    # if article.author_id != current_user.id:
    #     flash('You can only edit your own articles', 'error')
    #     return redirect(url_for('web.article_detail', article_id=article_id))
    
    if request.method == 'POST':
        article.title = request.form.get('title')
        article.content = request.form.get('content')
        
        # Handle Image Upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                upload_result = CloudinaryService.upload_image(file)
                if upload_result['success']:
                    article.image_url = upload_result['url']
                else:
                    flash(f'Gagal mengupload gambar: {upload_result.get("message")}', 'error')
                    return render_template('edit.html', article=article)
                    
        db.session.commit()
        
        flash('Article updated successfully!', 'success')
        # Redirect to admin detail view
        return redirect(url_for('web.dashboard_article_detail', article_id=article_id))
    
    return render_template('edit.html', article=article, stats=get_dashboard_stats())

@web_bp.route('/dashboard/articles/<int:article_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_article(article_id):
    """Delete article (admin and author only)"""
    article = Article.query.get_or_404(article_id)
    
    # Author check removed for admins
    # if article.author_id != current_user.id:
    #     flash('You can only delete your own articles', 'error')
    #     return redirect(url_for('web.article_detail', article_id=article_id))
    
    db.session.delete(article)
    db.session.commit()
    
    flash('Article deleted successfully!', 'success')
    return redirect(url_for('web.dashboard_articles'))


@web_bp.route('/dashboard/articles/<int:article_id>', methods=['GET'])
@login_required
@admin_required
def dashboard_article_detail(article_id):
    """Admin view of article detail"""
    article = Article.query.get_or_404(article_id)
    return render_template('detail_admin.html', article=article, stats=get_dashboard_stats())


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
            return redirect(url_for('web.index'))
        return redirect(url_for('web.index'))
        
    except Exception as e:
        flash('OAuth error occurred', 'error')
        return redirect(url_for('web.login'))

# ================= CATEGORY ROUTES =================

@web_bp.route('/dashboard/categories', methods=['GET'])
@login_required
@admin_required
def dashboard_categories():
    """Admin dashboard categories management page"""
    page = request.args.get('page', 1, type=int)
    categories = Category.query.order_by(Category.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('manage_categories.html', categories=categories, stats=get_dashboard_stats())

@web_bp.route('/dashboard/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    """Create category page (admin only)"""
    if request.method == 'POST':
        name = request.form.get('name')
        
        if Category.query.filter_by(name=name).first():
            flash('Kategori dengan nama tersebut sudah ada!', 'error')
            return render_template('create_category.html', stats=get_dashboard_stats())

        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        
        flash('Kategori berhasil ditambahkan!', 'success')
        return redirect(url_for('web.dashboard_categories'))
    
    return render_template('create_category.html', stats=get_dashboard_stats())

@web_bp.route('/dashboard/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """Edit category page (admin only)"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        existing = Category.query.filter_by(name=name).first()
        if existing and existing.id != category.id:
            flash('Kategori dengan nama tersebut sudah ada!', 'error')
            return render_template('edit_category.html', category=category, stats=get_dashboard_stats())
            
        category.name = name
        db.session.commit()
        
        flash('Kategori berhasil diperbarui!', 'success')
        return redirect(url_for('web.dashboard_categories'))
    
    return render_template('edit_category.html', category=category, stats=get_dashboard_stats())

@web_bp.route('/dashboard/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete category (admin only)"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has medicines
    if category.medicines:
         # Optional: Handle differently, e.g., set medicines' category to null or block deletion
         flash('Kategori ini terhubung dengan obat. Hapus obat atau ubah kategorinya terlebih dahulu.', 'error')
         return redirect(url_for('web.dashboard_categories'))

    db.session.delete(category)
    db.session.commit()
    
    flash('Kategori berhasil dihapus!', 'success')
    return redirect(url_for('web.dashboard_categories'))


# ================= MEDICINE ROUTES =================

@web_bp.route('/dashboard/medicines', methods=['GET'])
@login_required
@admin_required
def dashboard_medicines():
    """Admin dashboard medicines management page"""
    page = request.args.get('page', 1, type=int)
    medicines = Medicine.query.order_by(Medicine.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('manage_medicines.html', medicines=medicines, stats=get_dashboard_stats())

@web_bp.route('/dashboard/medicines/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_medicine():
    """Create medicine page (admin only)"""
    categories = Category.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        try:
            price = float(request.form.get('price', 0))
        except ValueError:
            price = 0.0
        category_id = request.form.get('category_id')
        
        # Handle Image Upload
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                upload_result = CloudinaryService.upload_image(file)
                if upload_result['success']:
                    image_url = upload_result['url']
                else:
                    flash(f'Gagal mengupload gambar: {upload_result.get("message")}', 'error')
                    return render_template('create_medicine.html', categories=categories, stats=get_dashboard_stats())
        
        medicine = Medicine(
            name=name, 
            description=description, 
            price=price, 
            category_id=category_id if category_id else None,
            image_url=image_url
        )
        db.session.add(medicine)
        db.session.commit()
        
        flash('Obat berhasil ditambahkan!', 'success')
        return redirect(url_for('web.dashboard_medicines'))
    
    return render_template('create_medicine.html', categories=categories, stats=get_dashboard_stats())

@web_bp.route('/dashboard/medicines/<int:medicine_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_medicine(medicine_id):
    """Edit medicine page (admin only)"""
    medicine = Medicine.query.get_or_404(medicine_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        medicine.name = request.form.get('name')
        medicine.description = request.form.get('description')
        try:
            medicine.price = float(request.form.get('price', 0))
        except ValueError:
            pass 
        
        cat_id = request.form.get('category_id')
        medicine.category_id = cat_id if cat_id else None
        
        # Handle Image Upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                upload_result = CloudinaryService.upload_image(file)
                if upload_result['success']:
                    medicine.image_url = upload_result['url']
                else:
                    flash(f'Gagal mengupload gambar: {upload_result.get("message")}', 'error')
                    return render_template('edit_medicine.html', medicine=medicine, categories=categories, stats=get_dashboard_stats())
        
        db.session.commit()
        
        flash('Data obat berhasil diperbarui!', 'success')
        return redirect(url_for('web.dashboard_medicines'))
    
    return render_template('edit_medicine.html', medicine=medicine, categories=categories, stats=get_dashboard_stats())

@web_bp.route('/dashboard/medicines/<int:medicine_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_medicine(medicine_id):
    """Delete medicine (admin only)"""
    medicine = Medicine.query.get_or_404(medicine_id)
    
    db.session.delete(medicine)
    db.session.commit()
    
    flash('Obat berhasil dihapus!', 'success')
    return redirect(url_for('web.dashboard_medicines'))
