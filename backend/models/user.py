# -*- coding: utf-8 -*-
"""
用户模型
"""
from utils.db import db
from datetime import datetime

class User(db.Model):
    """用户基础表"""
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'teacher', 'admin'), default='student', nullable=False)
    status = db.Column(db.SmallInteger, default=1)  # 0-禁用, 1-启用
    last_login_at = db.Column(db.TIMESTAMP, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    teacher = db.relationship('Teacher', backref='user', uselist=False, lazy='joined')
    student = db.relationship('Student', backref='user', uselist=False, lazy='joined')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'last_login_at': self.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_login_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    def get_profile(self):
        """获取用户完整资料"""
        data = self.to_dict()
        if self.role == 'teacher' and self.teacher:
            data['profile'] = self.teacher.to_dict()
        elif self.role == 'student' and self.student:
            data['profile'] = self.student.to_dict()
        return data
