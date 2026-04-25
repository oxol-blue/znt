# -*- coding: utf-8 -*-
"""
Database connection module
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    """Initialize database"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("Database tables created")

def check_db_connection():
    """Check database connection"""
    try:
        db.session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def get_db_session():
    """Get database session for AI tools"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import config
    
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()
