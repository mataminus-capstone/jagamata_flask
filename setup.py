"""
Setup script untuk inisialisasi database dan admin user
Jalankan: python setup.py
"""
import os
from dotenv import load_dotenv
from app import create_app
from models import db, User

load_dotenv()

def init_db():
    """Initialize database dengan sample data"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created: username='admin', password='admin123'")
        else:
            print("✓ Admin user already exists")
        
        # Create sample regular user
        user = User.query.filter_by(username='user').first()
        if not user:
            user = User(
                username='user',
                email='user@example.com',
                role='user'
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            print("✓ Regular user created: username='user', password='user123'")
        else:
            print("✓ Regular user already exists")

if __name__ == '__main__':
    try:
        init_db()
        print("\n✓ Setup completed successfully!")
        print("\nSilakan jalankan: python app.py")
    except Exception as e:
        print(f"✗ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
