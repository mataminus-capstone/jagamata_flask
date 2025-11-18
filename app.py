import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from config import config
from models import db, bcrypt, User
from routes import auth_bp, article_bp, admin_bp, home_bp
from chatbot_model import chatbot

def create_app(config_name='development'):
    app = Flask(__name__)
    
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    bcrypt.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu!'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(admin_bp)
    
    chatbot.init_app(app)
    
    @app.context_processor
    def inject_user():
        return {'current_user': current_user}
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=True, host='127.0.0.1', port=5000)
