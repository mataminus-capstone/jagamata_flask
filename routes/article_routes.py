from flask import Blueprint, request
from controllers.article_controller import ArticleController

article_bp = Blueprint('article', __name__, url_prefix='/api/articles')


@article_bp.route('/', methods=['GET', 'POST'])
def handle_articles():
    """Get articles (GET) or create article (POST)"""
    if request.method == 'GET':
        return ArticleController.get_articles()
    else:
        return ArticleController.create_article()

@article_bp.route('/<int:article_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def handle_article_detail(article_id):
    """Get, update, or delete specific article"""
    if request.method == 'GET':
        return ArticleController.get_article(article_id)
    elif request.method in ['PUT', 'PATCH']:
        return ArticleController.update_article(article_id)
    else:
        return ArticleController.delete_article(article_id)
