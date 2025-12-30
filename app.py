import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_login import LoginManager
from config import config
from models import db, bcrypt, User
from services.chatbot_service import chatbot
from services.auth_service import google_oauth, email_service

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name='development'):
    app = Flask(__name__)
    
    app.config.from_object(config[config_name])
    
    CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "PATCH"], allow_headers=["Content-Type", "Authorization"])
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    google_oauth.init_app(app)
    email_service.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'web.login'
    
    # Register API blueprints
    from routes.auth_routes import auth_bp
    from routes.chatbot_routes import chatbot_bp
    from routes.article_routes import article_bp
    from routes.user_routes import user_bp  
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(user_bp)
    
    from routes.web_routes import web_bp
    app.register_blueprint(web_bp)
    
    # Initialize chatbot
    chatbot.init_app(app)
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error': 'Not Found'
        }), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': 'Server Error'
        }), 500
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'error': 'Method Not Allowed'
        }), 405
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    port = int(os.getenv('PORT'))
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=os.getenv('FLASK_ENV') == 'development', host='0.0.0.0', port=port)
