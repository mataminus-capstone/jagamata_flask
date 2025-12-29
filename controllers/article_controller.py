from flask import request, jsonify, current_app
from models import db, Article, User
from datetime import datetime
from services.jwt_service import JWTService


class ArticleController:
    
    @staticmethod
    def _get_current_user_from_token():
        """Helper: Extract and verify current user from JWT token"""
        token = JWTService.extract_token_from_headers(request.headers)
        
        if not token:
            return None, None
        
        payload = JWTService.verify_token(token)
        
        if not payload:
            return None, None
        
        user_id = payload.get('user_id')
        user = User.query.get(user_id)
        
        return user, payload.get('role')
    
    @staticmethod
    def get_articles():
        """Get all articles with pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            # Limit per_page to prevent abuse
            per_page = min(per_page, 100)
            
            articles_paginated = Article.query.order_by(Article.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            articles_data = [{
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'author': {
                    'id': article.author.id,
                    'username': article.author.username
                },
                'created_at': article.created_at.isoformat(),
                'updated_at': article.updated_at.isoformat() if article.updated_at else None
            } for article in articles_paginated.items]
            
            return jsonify({
                'success': True,
                'data': {
                    'articles': articles_data,
                    'pagination': {
                        'page': articles_paginated.page,
                        'per_page': articles_paginated.per_page,
                        'total': articles_paginated.total,
                        'pages': articles_paginated.pages,
                        'has_next': articles_paginated.has_next,
                        'has_prev': articles_paginated.has_prev
                    }
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Get articles error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat mengambil artikel.'
            }), 500
    
    @staticmethod
    def get_article(article_id):
        """Get article by ID"""
        try:
            article = Article.query.get(article_id)
            
            if not article:
                return jsonify({
                    'success': False,
                    'message': 'Artikel tidak ditemukan.'
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'author': {
                        'id': article.author.id,
                        'username': article.author.username
                    },
                    'created_at': article.created_at.isoformat(),
                    'updated_at': article.updated_at.isoformat() if article.updated_at else None
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Get article error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat mengambil artikel.'
            }), 500
    
    @staticmethod
    def create_article():
        """Create new article (admin only)"""
        try:
            user, user_role = ArticleController._get_current_user_from_token()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Token tidak ditemukan. Silakan login kembali!'
                }), 401
            
            if not user.is_admin():
                return jsonify({
                    'success': False,
                    'message': 'Hanya admin yang bisa membuat artikel!'
                }), 403
            
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            
            if not title or not content:
                return jsonify({
                    'success': False,
                    'message': 'Judul dan konten harus diisi!'
                }), 400
            
            # Create article
            article = Article(title=title, content=content, author_id=user.id)
            db.session.add(article)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Artikel berhasil dibuat!',
                'data': {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'author': {
                        'id': article.author.id,
                        'username': article.author.username
                    },
                    'created_at': article.created_at.isoformat()
                }
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"Create article error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat membuat artikel.'
            }), 500
    
    @staticmethod
    def update_article(article_id):
        """Update article (admin and author only)"""
        try:
            article = Article.query.get(article_id)
            
            if not article:
                return jsonify({
                    'success': False,
                    'message': 'Artikel tidak ditemukan.'
                }), 404
            
            user, user_role = ArticleController._get_current_user_from_token()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Token tidak ditemukan. Silakan login kembali!'
                }), 401
            
            # Check if user is admin AND author of the article
            if not user.is_admin() or article.author_id != user.id:
                return jsonify({
                    'success': False,
                    'message': 'Anda tidak punya akses untuk edit artikel ini!'
                }), 403
            
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            # Update fields
            if 'title' in data:
                article.title = data['title'].strip()
            if 'content' in data:
                article.content = data['content'].strip()
            
            article.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Artikel berhasil diupdate!',
                'data': {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'author': {
                        'id': article.author.id,
                        'username': article.author.username
                    },
                    'created_at': article.created_at.isoformat(),
                    'updated_at': article.updated_at.isoformat()
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Update article error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat update artikel.'
            }), 500
    
    @staticmethod
    def delete_article(article_id):
        """Delete article (admin and author only)"""
        try:
            article = Article.query.get(article_id)
            
            if not article:
                return jsonify({
                    'success': False,
                    'message': 'Artikel tidak ditemukan.'
                }), 404
            
            user, user_role = ArticleController._get_current_user_from_token()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Token tidak ditemukan. Silakan login kembali!'
                }), 401
            
            # Check if user is admin AND author of the article
            if not user.is_admin() or article.author_id != user.id:
                return jsonify({
                    'success': False,
                    'message': 'Anda tidak punya akses untuk hapus artikel ini!'
                }), 403
            
            db.session.delete(article)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Artikel berhasil dihapus!'
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Delete article error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan saat menghapus artikel.'
            }), 500
