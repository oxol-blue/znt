# -*- coding: utf-8 -*-
"""
智慧校园多Agent双端智能体系统 - 配置文件
"""
import os
from datetime import timedelta

# 数据库配置
DB_CONFIG = {
    'host': '85.137.245.183',
    'port': 3306,
    'user': 'znt',
    'password': 'znt',
    'database': 'znt',  # 数据库名改为 znt
    'charset': 'utf8mb4'
}

# 构建SQLALCHEMY_DATABASE_URI
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    f"?charset={DB_CONFIG['charset']}"
)

# JWT配置
JWT_SECRET_KEY = 'smart-campus-jwt-secret-key-2024'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# Flask配置
SECRET_KEY = 'smart-campus-secret-key-2024'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False  # 生产环境设为False

# CORS配置
CORS_ORIGINS = ['*']  # 生产环境应限制域名

# 分页配置
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# 借阅配置
MAX_BORROW_DAYS = 14  # 最大借阅天数
MAX_RENEW_COUNT = 2   # 最大续借次数
DAILY_FINE = 0.5      # 每日罚款金额

# DeepSeek AI API 配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-a3ee725100c243678a35284e0f39def2')
DEEPSEEK_API_BASE = 'https://api.deepseek.com/v1'
DEEPSEEK_MODEL = 'deepseek-chat'  # 可选: deepseek-chat, deepseek-coder
