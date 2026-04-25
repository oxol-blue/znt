# -*- coding: utf-8 -*-
"""场地预约路由模块"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from models import Venue, Reservation, User
from utils import login_required, teacher_required, db
from datetime import datetime

reservation_bp = Blueprint('reservation', __name__, url_prefix='/api/reservations')

@reservation_bp.route('/venues', methods=['GET'])
@login_required
def get_venues():
    venues = Venue.query.all()
    return jsonify({'code': 200, 'data': [v.to_dict() for v in venues]})

@reservation_bp.route('/', methods=['GET'])
@login_required
def get_reservations():
    user_id = request.current_user['user_id']
    role = request.current_user.get('role', 'student')
    
    # 使用 joinedload 预加载关联数据，避免 N+1 查询
    # 需要预加载 user.student 和 user.teacher 来获取申请人姓名
    query = Reservation.query.options(
        joinedload(Reservation.venue),
        joinedload(Reservation.user).joinedload(User.student),
        joinedload(Reservation.user).joinedload(User.teacher)
    )
    
    # 教师可以看到所有预约记录（用于审批）
    # 学生只能看到自己的预约记录
    if role == 'teacher':
        reservations = query.all()
    else:
        reservations = query.filter_by(user_id=user_id).all()
    
    return jsonify({'code': 200, 'data': {'items': [r.to_dict() for r in reservations]}})

@reservation_bp.route('/', methods=['POST'])
@login_required
def create_reservation():
    user_id = request.current_user['user_id']
    data = request.get_json()
    
    reservation = Reservation(
        venue_id=data['venue_id'],
        user_id=user_id,
        reserve_date=datetime.strptime(data['reserve_date'], '%Y-%m-%d').date(),
        start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
        end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
        purpose=data.get('purpose'),
        participants=data.get('participants', 1)
    )
    db.session.add(reservation)
    db.session.commit()
    return jsonify({'code': 200, 'message': '预约成功', 'data': reservation.to_dict()})

@reservation_bp.route('/<int:id>/approve', methods=['POST'])
@teacher_required
def approve_reservation(id):
    data = request.get_json()
    reservation = Reservation.query.get(id)
    reservation.status = 'approved' if data.get('action') == 'approve' else 'rejected'
    reservation.approver_id = request.current_user['user_id']
    db.session.commit()
    return jsonify({'code': 200, 'message': '审批完成'})
