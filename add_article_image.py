from app import create_app
from models import db
from sqlalchemy import text
import os

def migrate_article_image():
    """Add image_url column to articles table"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        print("Starting article image migration...")
        try:
            # Check if column exists
            with db.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_NAME = 'articles' AND COLUMN_NAME = 'image_url'"
                ))
                
                if result.scalar() == 0:
                    print("Adding image_url column to articles table...")
                    conn.execute(text("ALTER TABLE articles ADD COLUMN image_url VARCHAR(512) NULL"))
                    conn.commit()
                    print("✓ image_url column added successfully!")
                else:
                    print("✓ image_url column already exists")
                    
        except Exception as e:
            print(f"✗ Migration failed: {e}")

if __name__ == '__main__':
    migrate_article_image()
