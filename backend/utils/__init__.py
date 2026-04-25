# -*- coding: utf-8 -*-
"""
工具函数初始化
"""
from utils.db import db, init_db, check_db_connection
from utils.jwt_auth import (
    generate_token, decode_token, login_required, 
    role_required, teacher_required, student_required, admin_required
)
from utils.validators import (
    validate_email, validate_phone, validate_student_no, validate_teacher_no,
    validate_isbn, validate_date, validate_time, sanitize_input,
    check_sensitive_words, validate_pagination
)

__all__ = [
    'db', 'init_db', 'check_db_connection',
    'generate_token', 'decode_token', 'login_required', 
    'role_required', 'teacher_required', 'student_required', 'admin_required',
    'validate_email', 'validate_phone', 'validate_student_no', 'validate_teacher_no',
    'validate_isbn', 'validate_date', 'validate_time', 'sanitize_input',
    'check_sensitive_words', 'validate_pagination'
]
