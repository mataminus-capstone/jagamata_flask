from flask import Blueprint
from flask_login import login_required
from controllers import (
    register_controller, login_controller, logout_controller,
    dashboard_controller, article_detail_controller,
    create_article_controller, edit_article_controller, delete_article_controller,
    home_controller
)

# ============ HOME ROUTES ============
home_bp = Blueprint('home', __name__)

@home_bp.route('/', methods=['GET'])
def index():
    return home_controller()

# ============ AUTH ROUTES ============
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    return register_controller()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    return login_controller()

@auth_bp.route('/logout', methods=['GET'])
@login_required
def logout():
    return logout_controller()


# ============ HEALTH CONTENT ROUTES ============
article_bp = Blueprint('article', __name__, url_prefix='/articles')

@article_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    return dashboard_controller()

@article_bp.route('/<int:article_id>', methods=['GET'])
@login_required
def detail(article_id):
    return article_detail_controller(article_id)

@article_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    return create_article_controller()

@article_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(article_id):
    return edit_article_controller(article_id)

@article_bp.route('/<int:article_id>/delete', methods=['POST'])
@login_required
def delete(article_id):
    return delete_article_controller(article_id)

# ============ CHATBOT ROUTES ============
# @home_bp.route('/chatbot', methods=['POST'])
# def chatbot():
#     return chatbot_controller()