# -*- coding: utf-8 -*-
"""
预约记录模型
"""
from utils.db import db
from datetime import datetime

class Reservation(db.Model):
    """场地预约记录表"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    venue_id = db.Column(db.BigInteger, db.ForeignKey('venues.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    reserve_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    purpose = db.Column(db.String(255), nullable=True)
    participants = db.Column(db.Integer, default=1)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'cancelled', 'completed'), default='pending')
    approver_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.TIMESTAMP, nullable=True)
    reject_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    # venue 关联通过 Venue 模型的 backref='venue' 自动创建
    # user 关联通过 User 模型的 backref 访问
    
    def to_dict(self):
        # 获取场地名称
        venue_name = None
        if hasattr(self, 'venue') and self.venue:
            venue_name = self.venue.name
        
        return {
            'id': self.id,
            'venue_id': self.venue_id,
            'venue_name': venue_name,
            'venue': self.venue.to_dict() if hasattr(self, 'venue') and self.venue else None,
            'user_id': self.user_id,
            'applicant_name': None,  # 简化处理，通过前端或单独查询获取
            'reserve_date': self.reserve_date.strftime('%Y-%m-%d') if self.reserve_date else None,
            'start_time': str(self.start_time) if self.start_time else None,
            'end_time': str(self.end_time) if self.end_time else None,
            'purpose': self.purpose,
            'participants': self.participants,
            'status': self.status,
            'approver_id': self.approver_id,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'reject_reason': self.reject_reason
        }
