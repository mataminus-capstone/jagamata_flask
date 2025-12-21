from flask import request, jsonify, current_app
from models import db, Article, User
from datetime import datetime

class ArticleController:
    
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
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            author_id = data.get('author_id')  # TODO: Get from JWT token
            
            if not title or not content:
                return jsonify({
                    'success': False,
                    'message': 'Judul dan konten harus diisi!'
                }), 400
            
            if not author_id:
                return jsonify({
                    'success': False,
                    'message': 'author_id diperlukan (sementara). Implementasikan JWT untuk production.'
                }), 400
            
            # Verify user exists and is admin
            user = User.query.get(author_id)
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User tidak ditemukan.'
                }), 404
            
            if not user.is_admin():
                return jsonify({
                    'success': False,
                    'message': 'Hanya admin yang bisa membuat artikel!'
                }), 403
            
            # Create article
            article = Article(title=title, content=content, author_id=author_id)
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
        """Update article (admin only)"""
        try:
            article = Article.query.get(article_id)
            
            if not article:
                return jsonify({
                    'success': False,
                    'message': 'Artikel tidak ditemukan.'
                }), 404
            
            data = request.get_json(force=True, silent=True)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON format'
                }), 400
            
            # TODO: Verify user is admin and is the author
            user_id = data.get('user_id')  # Get from JWT token in production
            if user_id:
                user = User.query.get(user_id)
                if not user or not user.is_admin() or article.author_id != user_id:
                    return jsonify({
                        'success': False,
                        'message': 'Anda tidak punya akses untuk edit artikel ini!'
                    }), 403
            
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
        """Delete article (admin only)"""
        try:
            article = Article.query.get(article_id)
            
            if not article:
                return jsonify({
                    'success': False,
                    'message': 'Artikel tidak ditemukan.'
                }), 404
            
            # TODO: Verify user is admin and is the author
            data = request.get_json(force=True, silent=True) or {}
            user_id = data.get('user_id')  # Get from JWT token in production
            
            if user_id:
                user = User.query.get(user_id)
                if not user or not user.is_admin() or article.author_id != user_id:
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
