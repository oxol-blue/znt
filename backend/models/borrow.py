# -*- coding: utf-8 -*-
"""
借阅记录模型
"""
from utils.db import db
from datetime import datetime

class Borrow(db.Model):
    """图书借阅记录表"""
    __tablename__ = 'borrows'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    book_id = db.Column(db.BigInteger, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    renew_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('borrowed', 'returned', 'overdue'), default='borrowed')
    fine_amount = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    # book 关联通过 Book 模型的 backref='book' 自动创建
    # user 关联通过 User 模型的 backref 访问
    
    def to_dict(self):
        # 获取图书标题
        book_title = None
        if hasattr(self, 'book') and self.book:
            book_title = self.book.title
        
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': book_title,
            'book': self.book.to_dict() if hasattr(self, 'book') and self.book else None,
            'user_id': self.user_id,
            'borrow_date': self.borrow_date.strftime('%Y-%m-%d') if self.borrow_date else None,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'return_date': self.return_date.strftime('%Y-%m-%d') if self.return_date else None,
            'renew_count': self.renew_count,
            'status': self.status,
            'fine_amount': float(self.fine_amount)
        }
