# -*- coding: utf-8 -*-
"""
场地模型
"""
from utils.db import db
from datetime import datetime

class Venue(db.Model):
    """校园场地资源表"""
    __tablename__ = 'venues'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum('library', 'lab', 'classroom', 'meeting_room', 'gym'), nullable=False)
    building = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.Integer, default=1)
    room_no = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    facilities = db.Column(db.JSON, nullable=True)
    open_time = db.Column(db.Time, default='08:00:00')
    close_time = db.Column(db.Time, default='22:00:00')
    status = db.Column(db.Enum('available', 'occupied', 'maintenance'), default='available')
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    reservations = db.relationship('Reservation', backref='venue', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'building': self.building,
            'floor': self.floor,
            'room_no': self.room_no,
            'capacity': self.capacity,
            'facilities': self.facilities,
            'open_time': str(self.open_time) if self.open_time else None,
            'close_time': str(self.close_time) if self.close_time else None,
            'status': self.status,
            'description': self.description
        }
