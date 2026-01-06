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
    
    app.url_map.strict_slashes = False
    
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=False,
         max_age=3600)
    
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
    
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
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
    port = int(os.getenv('PORT', 5000))
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=os.getenv('FLASK_ENV') == 'development', host='0.0.0.0', port=port)
