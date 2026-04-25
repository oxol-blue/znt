# -*- coding: utf-8 -*-
"""
消息通知模型
"""
from utils.db import db
from datetime import datetime

class Notification(db.Model):
    """消息通知表"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=True)
    receiver_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=True)
    target_type = db.Column(db.Enum('all', 'student', 'teacher', 'specific'), default='specific')
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum('system', 'library', 'task', 'reservation', 'announcement'), default='system')
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent'), default='normal')
    is_read = db.Column(db.SmallInteger, default=0)
    read_at = db.Column(db.TIMESTAMP, nullable=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    
    # 关联
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications', lazy='joined')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_notifications', lazy='joined')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.teacher.name if self.sender and self.sender.teacher else 
                          (self.sender.student.name if self.sender and self.sender.student else '系统'),
            'receiver_id': self.receiver_id,
            'target_type': self.target_type,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'priority': self.priority,
            'is_read': self.is_read,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M:%S') if self.read_at else None,
            'attachment_url': self.attachment_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
