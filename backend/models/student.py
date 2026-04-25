# -*- coding: utf-8 -*-
"""
学生模型
"""
from utils.db import db
from datetime import datetime

class Student(db.Model):
    """学生信息表"""
    __tablename__ = 'students'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    student_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    dormitory = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'student_no': self.student_no,
            'name': self.name,
            'major': self.major,
            'class_name': self.class_name,
            'grade': self.grade,
            'phone': self.phone,
            'email': self.email,
            'dormitory': self.dormitory
        }
