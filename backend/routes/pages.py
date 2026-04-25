# -*- coding: utf-8 -*-
"""
页面渲染蓝图 - 直接从数据库获取数据渲染HTML
"""
from flask import Blueprint, render_template_string, request, session, redirect, url_for
from models import Book, Task, Notification, Reservation, Venue, User, Student, Teacher
from utils import db
import json

page_bp = Blueprint('pages', __name__)

# 读取HTML模板
def read_template(template_name):
    import os
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

# 检查登录状态
def check_login():
    return 'user_id' in session

# 学生端 - 图书馆页面
@page_bp.route('/student/library.html')
def student_library():
    if not check_login():
        return redirect('/index.html')
    
    # 直接从数据库获取图书数据
    books = Book.query.all()
    books_data = [book.to_dict() for book in books]
    
    # 读取HTML模板
    html = read_template('student/library.html')
    
    # 替换数据占位符
    html = html.replace('{{ books_data }}', json.dumps(books_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html

# 教师端 - 图书管理页面
@page_bp.route('/teacher/library.html')
def teacher_library():
    if not check_login():
        return redirect('/index.html')
    
    # 直接从数据库获取图书数据
    books = Book.query.all()
    books_data = [book.to_dict() for book in books]
    
    # 读取HTML模板
    html = read_template('teacher/library.html')
    
    # 替换数据占位符
    html = html.replace('{{ books_data }}', json.dumps(books_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html

# 学生端 - 任务页面
@page_bp.route('/student/tasks.html')
def student_tasks():
    if not check_login():
        return redirect('/index.html')
    
    user_id = session.get('user_id')
    # 直接从数据库获取任务数据
    tasks = Task.query.filter(Task.target_type == 'all').all()
    tasks_data = [task.to_dict() for task in tasks]
    
    # 读取HTML模板
    html = read_template('student/tasks.html')
    
    # 替换数据占位符
    html = html.replace('{{ tasks_data }}', json.dumps(tasks_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html

# 教师端 - 任务管理页面
@page_bp.route('/teacher/tasks.html')
def teacher_tasks():
    if not check_login():
        return redirect('/index.html')
    
    # 直接从数据库获取任务数据
    tasks = Task.query.all()
    tasks_data = [task.to_dict() for task in tasks]
    
    # 读取HTML模板
    html = read_template('teacher/tasks.html')
    
    # 替换数据占位符
    html = html.replace('{{ tasks_data }}', json.dumps(tasks_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html

# 学生端 - 场地预约页面
@page_bp.route('/student/reservations.html')
def student_reservations():
    if not check_login():
        return redirect('/index.html')
    
    # 直接从数据库获取场地数据
    venues = Venue.query.all()
    venues_data = [venue.to_dict() for venue in venues]
    
    # 读取HTML模板
    html = read_template('student/reservations.html')
    
    # 替换数据占位符
    html = html.replace('{{ venues_data }}', json.dumps(venues_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html

# 教师端 - 预约审批页面
@page_bp.route('/teacher/reservations.html')
def teacher_reservations():
    if not check_login():
        return redirect('/index.html')
    
    # 直接从数据库获取预约数据
    reservations = Reservation.query.all()
    reservations_data = [reservation.to_dict() for reservation in reservations]
    
    # 读取HTML模板
    html = read_template('teacher/reservations.html')
    
    # 替换数据占位符
    html = html.replace('{{ reservations_data }}', json.dumps(reservations_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html

# 学生端 - 消息中心页面
@page_bp.route('/student/notifications.html')
def student_notifications():
    if not check_login():
        return redirect('/index.html')
    
    user_id = session.get('user_id')
    # 直接从数据库获取通知数据
    notifications = Notification.query.filter(
        (Notification.receiver_id == user_id) | (Notification.receiver_id == None)
    ).all()
    notifications_data = [notification.to_dict() for notification in notifications]
    
    # 读取HTML模板
    html = read_template('student/notifications.html')
    
    # 替换数据占位符
    html = html.replace('{{ notifications_data }}', json.dumps(notifications_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html

# 教师端 - 通知发布页面
@page_bp.route('/teacher/notifications.html')
def teacher_notifications():
    if not check_login():
        return redirect('/index.html')
    
    # 直接从数据库获取通知数据
    notifications = Notification.query.all()
    notifications_data = [notification.to_dict() for notification in notifications]
    
    # 读取HTML模板
    html = read_template('teacher/notifications.html')
    
    # 替换数据占位符
    html = html.replace('{{ notifications_data }}', json.dumps(notifications_data, ensure_ascii=False))
    html = html.replace('{{ loading }}', 'false')
    
    return html
