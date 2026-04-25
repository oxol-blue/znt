# -*- coding: utf-8 -*-
"""
认证路由模块
"""
from flask import Blueprint, request, jsonify
import bcrypt
from datetime import datetime
from models import User, Teacher, Student
from utils import generate_token, login_required, db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data:
        return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401
    
    if user.status == 0:
        return jsonify({'code': 403, 'message': '账号已被禁用'}), 403
    
    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401
    
    user.last_login_at = datetime.now()
    db.session.commit()
    
    token = generate_token(user.id, user.username, user.role)
    
    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': token,
            'user': user.get_profile()
        }
    })

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户信息"""
    user_id = request.current_user['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    return jsonify({
        'code': 200,
        'message': '获取成功',
        'data': user.get_profile()
    })

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not old_password or not new_password:
        return jsonify({'code': 400, 'message': '原密码和新密码不能为空'}), 400
    
    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '新密码长度不能少于6位'}), 400
    
    user = User.query.get(user_id)
    
    if not bcrypt.checkpw(old_password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'code': 400, 'message': '原密码错误'}), 400
    
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    user.password = hashed.decode('utf-8')
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '密码修改成功'})
