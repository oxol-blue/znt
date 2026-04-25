# -*- coding: utf-8 -*-
"""
数据验证工具模块
"""
import re
from datetime import datetime, date

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """验证手机号格式"""
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_student_no(student_no):
    """验证学号格式"""
    # 学号通常为10位数字
    pattern = r'^\d{10}$'
    return re.match(pattern, student_no) is not None

def validate_teacher_no(teacher_no):
    """验证工号格式"""
    # 工号通常为T开头加3位数字
    pattern = r'^T\d{3}$'
    return re.match(pattern, teacher_no) is not None

def validate_isbn(isbn):
    """验证ISBN格式"""
    # 支持 ISBN-10 和 ISBN-13
    pattern = r'^(?:ISBN[-]?(?:13|10)?:? )?(?=[0-9X]{10}$|(?=(?:[0-9]+[- ]){3})[- 0-9X]{13}$|97[89][0-9]{10}$|(?=(?:[0-9]+[- ]){4})[- 0-9]{17}$)(?:97[89][- ]?)?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9X]$'
    return re.match(pattern, isbn) is not None or len(isbn.replace('-', '')) in [10, 13]

def validate_date(date_str, format='%Y-%m-%d'):
    """验证日期格式"""
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def validate_time(time_str, format='%H:%M:%S'):
    """验证时间格式"""
    try:
        datetime.strptime(time_str, format)
        return True
    except ValueError:
        return False

def sanitize_input(text, max_length=None):
    """清理用户输入，防止XSS"""
    if not text:
        return text
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 转义特殊字符
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    # 限制长度
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

def check_sensitive_words(text):
    """检查敏感词（简化版）"""
    sensitive_words = [
        '暴力', '恐怖', '赌博', '毒品', '色情', '淫秽',
        '诈骗', '黑客', '攻击', '破解', '作弊'
    ]
    
    text_lower = text.lower()
    found_words = []
    
    for word in sensitive_words:
        if word in text_lower:
            found_words.append(word)
    
    return found_words

def validate_pagination(page, page_size):
    """验证分页参数"""
    try:
        page = int(page)
        page_size = int(page_size)
        
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100
            
        return page, page_size
    except (ValueError, TypeError):
        return 1, 10
