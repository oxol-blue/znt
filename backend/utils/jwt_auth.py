# -*- coding: utf-8 -*-
"""
JWT认证工具模块
"""
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from config import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES

def generate_token(user_id, username, role):
    """生成JWT Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES,
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    return token

def decode_token(token):
    """解码JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token已过期
    except jwt.InvalidTokenError:
        return None  # Token无效

def get_token_from_header():
    """从请求头中获取Token"""
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    return None

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 允许 OPTIONS 请求通过（CORS 预检）
        if request.method == 'OPTIONS':
            response = jsonify({'code': 200})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            return response
        
        token = get_token_from_header()
        if not token:
            return jsonify({'code': 401, 'message': '缺少认证Token'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': 'Token无效或已过期'}), 401
        
        # 将用户信息存入请求上下文
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """角色验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 允许 OPTIONS 请求通过（CORS 预检）
            if request.method == 'OPTIONS':
                response = jsonify({'code': 200})
                response.headers.add('Access-Control-Allow-Origin', '*')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
                response.headers.add('Access-Control-Allow-Methods', 'POST, PUT, DELETE, OPTIONS')
                return response
            
            token = get_token_from_header()
            if not token:
                return jsonify({'code': 401, 'message': '缺少认证Token'}), 401
            
            payload = decode_token(token)
            if not payload:
                return jsonify({'code': 401, 'message': 'Token无效或已过期'}), 401
            
            if payload['role'] not in allowed_roles:
                return jsonify({'code': 403, 'message': '权限不足'}), 403
            
            request.current_user = payload
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 便捷装饰器
teacher_required = role_required(['teacher', 'admin'])
student_required = role_required(['student'])
admin_required = role_required(['admin'])
