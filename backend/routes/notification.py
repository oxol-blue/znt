# -*- coding: utf-8 -*-
"""消息通知路由模块"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import Notification
from utils import login_required, teacher_required, db

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')

@notification_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    user_id = request.current_user['user_id']
    role = request.current_user['role']
    
    query = Notification.query.filter(
        db.or_(
            Notification.receiver_id == user_id,
            db.and_(Notification.receiver_id.is_(None), Notification.target_type.in_(['all', role]))
        )
    )
    notifications = query.order_by(Notification.created_at.desc()).all()
    return jsonify({'code': 200, 'data': {'items': [n.to_dict() for n in notifications]}})

@notification_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    user_id = request.current_user['user_id']
    role = request.current_user['role']
    count = Notification.query.filter(
        Notification.is_read == 0,
        db.or_(
            Notification.receiver_id == user_id,
            db.and_(Notification.receiver_id.is_(None), Notification.target_type.in_(['all', role]))
        )
    ).count()
    return jsonify({'code': 200, 'data': {'unread_count': count}})

@notification_bp.route('/', methods=['POST'])
@teacher_required
def create_notification():
    data = request.get_json()
    notif = Notification(
        sender_id=request.current_user['user_id'],
        target_type=data.get('target_type', 'all'),
        title=data['title'],
        content=data['content'],
        type=data.get('type', 'announcement'),
        priority=data.get('priority', 'normal')
    )
    db.session.add(notif)
    db.session.commit()
    return jsonify({'code': 200, 'message': '发送成功', 'data': notif.to_dict()})

@notification_bp.route('/<int:id>/read', methods=['PUT'])
@login_required
def mark_read(id):
    notif = Notification.query.get(id)
    if notif:
        notif.is_read = 1
        notif.read_at = datetime.now()
        db.session.commit()
    return jsonify({'code': 200, 'message': '标记成功'})
