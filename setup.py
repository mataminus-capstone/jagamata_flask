"""
Setup script untuk inisialisasi database dan admin user
Jalankan: python setup.py
"""
import os
from dotenv import load_dotenv
from app import create_app
from models import db, User

load_dotenv()

def migrate_remove_username_unique():
    """Remove unique constraint from username column"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            # Check if username constraint exists
            result = db.session.execute(text(
                "SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                "WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'username' AND CONSTRAINT_NAME != 'PRIMARY'"
            ))
            
            constraint = result.scalar()
            
            if constraint:
                print(f"Removing unique constraint from username: {constraint}")
                db.session.execute(text(
                    f"ALTER TABLE users DROP CONSTRAINT {constraint}"
                ))
                db.session.commit()
                print("✓ Username unique constraint removed!")
                return True
            else:
                print("✓ Username constraint already handled")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"Note: Username constraint migration skipped: {str(e)}")
            # Don't fail the setup for this, continue

def migrate_oauth_columns():
    """Add OAuth columns to existing users table if they don't exist"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            # Check if oauth_provider column exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'oauth_provider'"
            ))
            
            if result.scalar() == 0:
                print("Adding OAuth columns to users table...")
                
                # Add new columns
                db.session.execute(text(
                    "ALTER TABLE users "
                    "ADD COLUMN oauth_provider VARCHAR(50), "
                    "ADD COLUMN oauth_id VARCHAR(255), "
                    "ADD COLUMN email_verified BOOLEAN DEFAULT FALSE, "
                    "ADD COLUMN verification_token VARCHAR(255), "
                    "ADD COLUMN reset_token VARCHAR(255), "
                    "ADD COLUMN reset_token_expiry DATETIME"
                ))
                
                # Add unique constraint
                db.session.execute(text(
                    "ALTER TABLE users "
                    "ADD UNIQUE INDEX idx_oauth_provider_id (oauth_provider, oauth_id)"
                ))
                
                db.session.commit()
                print("✓ OAuth columns added successfully!")
                return True
            else:
                print("✓ OAuth columns already exist")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error migrating OAuth columns: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

def migrate_user_profile_columns():
    """Add address and phone_number columns to existing users table if they don't exist"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            # Check if address column exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'address'"
            ))
            
            if result.scalar() == 0:
                print("Adding address and phone_number columns to users table...")
                
                # Add new columns
                db.session.execute(text(
                    "ALTER TABLE users "
                    "ADD COLUMN address VARCHAR(255), "
                    "ADD COLUMN phone_number VARCHAR(20)"
                ))
                
                db.session.commit()
                print("✓ Address and phone_number columns added successfully!")
                return True
            else:
                print("✓ Address and phone_number columns already exist")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error migrating user profile columns: {str(e)}")
            import traceback
            traceback.print_exc()
            # Do not raise here to allow setup to continue if it's just a column exists error that wasn't caught


def init_db():
    """Initialize database dengan sample data"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        migrate_remove_username_unique()
        migrate_oauth_columns()
        migrate_user_profile_columns()
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                email_verified=True  # Admin email is pre-verified
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created: email='admin@example.com', password='admin123'")
        else:
            print("✓ Admin user already exists")
        
        # Create sample regular user
        user = User.query.filter_by(email='user@example.com').first()
        if not user:
            user = User(
                username='user',
                email='user@example.com',
                role='user',
                email_verified=True  # Sample user email is pre-verified
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            print("✓ Regular user created: email='user@example.com', password='user123'")
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
