# -*- coding: utf-8 -*-
"""图书馆路由模块"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import Book, Borrow
from utils import login_required, teacher_required, db, validate_pagination
from config import MAX_BORROW_DAYS

library_bp = Blueprint('library', __name__, url_prefix='/api/library')

@library_bp.route('/books', methods=['GET'])
@login_required
def get_books():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '').strip()
    
    query = Book.query
    if keyword:
        query = query.filter(db.or_(Book.title.contains(keyword), Book.author.contains(keyword)))
    
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    return jsonify({
        'code': 200,
        'data': {
            'items': [book.to_dict() for book in pagination.items],
            'total': pagination.total
        }
    })

@library_bp.route('/books', methods=['POST'])
@teacher_required
def create_book():
    data = request.get_json()
    book = Book(**data)
    db.session.add(book)
    db.session.commit()
    return jsonify({'code': 200, 'message': '添加成功', 'data': book.to_dict()})

@library_bp.route('/borrow', methods=['POST'])
@login_required
def borrow_book():
    user_id = request.current_user['user_id']
    data = request.get_json()
    book_id = data.get('book_id')
    
    book = Book.query.get(book_id)
    if not book or book.available_quantity <= 0:
        return jsonify({'code': 400, 'message': '图书不可用'}), 400
    
    borrow = Borrow(
        book_id=book_id,
        user_id=user_id,
        borrow_date=datetime.now().date(),
        due_date=datetime.now().date() + timedelta(days=MAX_BORROW_DAYS)
    )
    book.available_quantity -= 1
    db.session.add(borrow)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '借阅成功', 'data': borrow.to_dict()})

@library_bp.route('/borrows', methods=['GET'])
@login_required
def get_borrows():
    user_id = request.current_user['user_id']
    borrows = Borrow.query.filter_by(user_id=user_id).all()
    return jsonify({'code': 200, 'data': {'items': [b.to_dict() for b in borrows]}})
