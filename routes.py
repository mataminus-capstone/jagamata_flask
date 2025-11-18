from flask import Blueprint
from flask_login import login_required
from controllers import (
    register_controller, login_controller, logout_controller,
    articles_controller, article_detail_controller,
    create_article_controller, edit_article_controller, delete_article_controller,
    home_controller, admin_dashboard_controller, chatbot_controller
)
from api_controllers import (
    api_register, api_login, api_articles, api_article_detail, api_chatbot
)

home_bp = Blueprint('home', __name__)

@home_bp.route('/', methods=['GET'])
def index():
    return home_controller()

@home_bp.route('/chatbot', methods=['POST', 'GET'])
def chatbot_endpoint(): 
    return chatbot_controller()

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

article_bp = Blueprint('article', __name__, url_prefix='/articles')

@article_bp.route('/', methods=['GET'])
@login_required
def articles():
    return articles_controller()

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

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return admin_dashboard_controller()

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/auth/register', methods=['POST'])
def api_register_route():
    return api_register()

@api_bp.route('/auth/login', methods=['POST'])
def api_login_route():
    return api_login()

@api_bp.route('/articles', methods=['GET'])
def api_articles_route():
    return api_articles()

@api_bp.route('/articles/<int:article_id>', methods=['GET'])
def api_article_detail_route(article_id):
    return api_article_detail(article_id)

@api_bp.route('/chatbot', methods=['POST'])
def api_chatbot_route():
    return api_chatbot()
