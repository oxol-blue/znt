# -*- coding: utf-8 -*-
"""
教师模型
"""
from utils.db import db
from datetime import datetime

class Teacher(db.Model):
    """教师信息表"""
    __tablename__ = 'teachers'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    teacher_no = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(50), nullable=True)  # 职称
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    office = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'teacher_no': self.teacher_no,
            'department': self.department,
            'title': self.title,
            'phone': self.phone,
            'email': self.email,
            'office': self.office
        }
