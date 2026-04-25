# -*- coding: utf-8 -*-
"""
任务模型
"""
from utils.db import db
from datetime import datetime

class Task(db.Model):
    """每日任务表"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    creator_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.Enum('all', 'student', 'teacher', 'specific'), nullable=False)
    target_users = db.Column(db.JSON, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    task_type = db.Column(db.Enum('daily', 'weekly', 'assignment', 'exam', 'activity'), default='daily')
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent'), default='normal')
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('draft', 'published', 'cancelled'), default='published')
    attachment_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    creator = db.relationship('User', backref='created_tasks', lazy='joined')
    completions = db.relationship('TaskCompletion', backref='task', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'creator_id': self.creator_id,
            'creator_name': self.creator.teacher.name if self.creator and self.creator.teacher else 
                           (self.creator.student.name if self.creator and self.creator.student else '未知'),
            'target_type': self.target_type,
            'target_users': self.target_users,
            'title': self.title,
            'content': self.content,
            'task_type': self.task_type,
            'priority': self.priority,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'status': self.status,
            'attachment_url': self.attachment_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class TaskCompletion(db.Model):
    """任务完成记录表"""
    __tablename__ = 'task_completions'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    task_id = db.Column(db.BigInteger, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    completed_at = db.Column(db.TIMESTAMP, default=datetime.now)
    completion_note = db.Column(db.Text, nullable=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    
    # 关联
    user = db.relationship('User', backref='task_completions', lazy='joined')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': self.user.student.name if self.user and self.user.student else 
                        (self.user.teacher.name if self.user and self.user.teacher else '未知'),
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'completion_note': self.completion_note,
            'attachment_url': self.attachment_url
        }
