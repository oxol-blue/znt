# -*- coding: utf-8 -*-
"""任务管理路由模块"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import Task, TaskCompletion, Notification
from utils import login_required, teacher_required, db

task_bp = Blueprint('task', __name__, url_prefix='/api/tasks')

@task_bp.route('/', methods=['GET'])
@login_required
def get_tasks():
    user_id = request.current_user['user_id']
    role = request.current_user['role']
    
    if role in ['teacher', 'admin']:
        tasks = Task.query.filter_by(creator_id=user_id).all()
    else:
        tasks = Task.query.filter(Task.status == 'published').all()
    
    result = []
    for task in tasks:
        task_dict = task.to_dict()
        completion = TaskCompletion.query.filter_by(task_id=task.id, user_id=user_id).first()
        task_dict['is_completed'] = completion is not None
        result.append(task_dict)
    
    return jsonify({'code': 200, 'data': {'items': result}})

@task_bp.route('/', methods=['POST'])
@teacher_required
def create_task():
    data = request.get_json()
    task = Task(
        creator_id=request.current_user['user_id'],
        title=data['title'],
        content=data['content'],
        task_type=data.get('task_type', 'daily'),
        target_type=data['target_type'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    )
    db.session.add(task)
    db.session.commit()

    # 创建对应的通知
    task_type_label = {
        'daily': '日常任务',
        'study': '学习任务',
        'activity': '活动任务',
        'exam': '考试任务'
    }.get(task.task_type, '新任务')

    target_type_label = {
        'all': '全体学生',
        'undergraduate': '本科生',
        'graduate': '研究生'
    }.get(task.target_type, '全体学生')

    notification = Notification(
        sender_id=request.current_user['user_id'],
        target_type='student' if task.target_type in ['all', 'undergraduate', 'graduate'] else task.target_type,
        title=f'【{task_type_label}】{task.title}',
        content=f'老师发布了一个新任务\n开始日期：{task.start_date}\n截止日期：{task.end_date}\n\n任务内容：\n{task.content[:200]}{"..." if len(task.content) > 200 else ""}',
        type='task',
        priority='normal'
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'code': 200, 'message': '发布成功', 'data': task.to_dict()})

@task_bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete_task(id):
    user_id = request.current_user['user_id']
    completion = TaskCompletion(task_id=id, user_id=user_id)
    db.session.add(completion)
    db.session.commit()
    return jsonify({'code': 200, 'message': '任务完成'})
