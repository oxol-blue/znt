# -*- coding: utf-8 -*-
"""
智慧校园多Agent双端智能体系统 - Flask应用入口
"""
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import config
import os
import traceback
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 获取前端目录路径（在 backend 的上级目录）
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

def create_app():
    """应用工厂函数"""
    logger.info("Starting create_app...")
    
    # 不设置 static_url_path=''，避免与 API 路由冲突
    app = Flask(__name__, static_folder=None)
    logger.info("Flask app created")
    
    # 加载配置
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ECHO'] = config.SQLALCHEMY_ECHO
    logger.info("Config loaded")
    
    # 启用CORS - 支持预检请求
    CORS(app, 
         origins=config.CORS_ORIGINS,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    logger.info("CORS enabled")
    
    # 初始化数据库
    from utils import init_db
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized")
    
    # 注册API蓝图（必须先于前端路由注册）
    from routes import register_blueprints
    logger.info("Registering blueprints...")
    register_blueprints(app)
    logger.info("Blueprints registered")
    
    # 注册页面蓝图
    from routes.pages import page_bp
    app.register_blueprint(page_bp)
    logger.info("Page blueprint registered")
    
    # 错误处理 - 改进版，显示详细错误
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'code': 404, 'message': '接口不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        # 打印详细错误信息到控制台
        logger.error(f"500 Error: {error}")
        logger.error(traceback.format_exc())
        return jsonify({
            'code': 500, 
            'message': '服务器内部错误',
            'error': str(error)
        }), 500
    
    # 捕获所有异常并打印
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled Exception: {error}")
        logger.error(traceback.format_exc())
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'error': str(error)
        }), 500
    
    # 健康检查
    @app.route('/api/health')
    def health_check():
        from utils import check_db_connection
        db_status = check_db_connection()
        return jsonify({
            'code': 200,
            'message': '服务运行正常',
            'data': {
                'database': 'connected' if db_status else 'disconnected'
            }
        })
    
    # 静态文件服务 - /assets 目录
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), filename)
    
    # 根路由 - 返回前端页面
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'index.html')
    
    # 前端页面路由 - 排除 API 路径
    @app.route('/<path:filename>')
    def frontend(filename):
        # API 路由不走这里
        if filename.startswith('api/'):
            return jsonify({'code': 404, 'message': '接口不存在'}), 404
        
        # 静态文件直接返回
        file_path = os.path.join(FRONTEND_DIR, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(FRONTEND_DIR, filename)
        else:
            # 如果是前端路由（如 /student/dashboard），返回 index.html 让前端处理
            return send_from_directory(FRONTEND_DIR, 'index.html')
    
    logger.info("App created successfully")
    return app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    print("Smart Campus System Starting...")
    print("API: http://localhost:5000")
    print("Frontend: http://localhost:5000/index.html")
    print("AI Assistant: http://localhost:5000/ai-assistant.html")
    print("")
    print("Test Accounts (username = password):")
    print("  Student: 2021001000 ~ 2021001003")
    print("  Teacher: T001 / T002")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)
