# -*- coding: utf-8 -*-
"""
图书模型
"""
from utils.db import db
from datetime import datetime

class Book(db.Model):
    """图书馆图书表"""
    __tablename__ = 'books'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100), nullable=True)
    publish_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    total_quantity = db.Column(db.Integer, default=1)
    available_quantity = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('available', 'borrowed', 'reserved', 'damaged'), default='available')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    borrows = db.relationship('Borrow', backref='book', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'publish_date': self.publish_date.strftime('%Y-%m-%d') if self.publish_date else None,
            'category': self.category,
            'location': self.location,
            'total_quantity': self.total_quantity,
            'available_quantity': self.available_quantity,
            'description': self.description,
            'status': self.status
        }
