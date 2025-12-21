from flask import Blueprint
from controllers.article_controller import ArticleController

article_bp = Blueprint('article', __name__, url_prefix='/api/articles')

@article_bp.route('/', methods=['GET'])
def get_articles():
    """Get all articles"""
    return ArticleController.get_articles()

@article_bp.route('/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Get article by ID"""
    return ArticleController.get_article(article_id)

@article_bp.route('/', methods=['POST'])
def create_article():
    """Create new article (admin only)"""
    return ArticleController.create_article()

@article_bp.route('/<int:article_id>', methods=['PUT', 'PATCH'])
def update_article(article_id):
    """Update article (admin only)"""
    return ArticleController.update_article(article_id)

@article_bp.route('/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """Delete article (admin only)"""
    return ArticleController.delete_article(article_id)
