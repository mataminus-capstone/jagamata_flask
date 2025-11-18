from flask import request, jsonify, current_app
from models import db, User, Article
from chatbot_model import chatbot

def api_register():
    try:
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON format'
            }), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email, username, dan password harus diisi!'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password minimal 6 karakter!'
            }), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': 'Username sudah terdaftar!'
            }), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'Email sudah terdaftar!'
            }), 400
        
        user = User(username=username, email=email, role='user')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registrasi berhasil! Silakan login.'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Register error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat registrasi.'
        }), 500

def api_login():
    try:
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid JSON format'
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username dan password harus diisi!'
            }), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            return jsonify({
                'success': True,
                'message': f'Selamat datang {user.username}!',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            }), 200
        
        return jsonify({
            'success': False,
            'message': 'Username atau password salah!'
        }), 401
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat login.'
        }), 500

def api_articles():
    try:
        articles = Article.query.order_by(Article.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'articles': [{
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'author': article.author.username,
                'created_at': article.created_at.isoformat(),
                'updated_at': article.updated_at.isoformat() if article.updated_at else None
            } for article in articles]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get articles error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil artikel.'
        }), 500

def api_article_detail(article_id):
    try:
        article = Article.query.get(article_id)
        
        if not article:
            return jsonify({
                'success': False,
                'message': 'Artikel tidak ditemukan.'
            }), 404
        
        return jsonify({
            'success': True,
            'article': {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'author': article.author.username,
                'created_at': article.created_at.isoformat(),
                'updated_at': article.updated_at.isoformat() if article.updated_at else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get article detail error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil detail artikel.'
        }), 500

def api_chatbot():
    try:
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({
                'success': False,
                'response': 'Invalid JSON format',
                'doctor': 'System',
                'confidence': 0
            }), 400
        
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'success': False,
                'response': 'Pesan tidak boleh kosong.',
                'doctor': 'System',
                'confidence': 0
            }), 400
        
        result = chatbot.predict(message)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'response': result['response'],
                'doctor': 'System',
                'confidence': 0
            }), 500
        
        return jsonify({
            'success': True,
            'response': result['response'],
            'doctor': result['doctor'],
            'confidence': result['confidence']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Chatbot error: {str(e)}")
        return jsonify({
            'success': False,
            'response': 'Terjadi kesalahan saat memproses pesan.',
            'doctor': 'System',
            'confidence': 0
        }), 500
