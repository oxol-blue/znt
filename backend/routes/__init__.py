# -*- coding: utf-8 -*-
"""
路由初始化
"""
from routes.auth import auth_bp
from routes.library import library_bp
from routes.notification import notification_bp
from routes.task import task_bp
from routes.reservation import reservation_bp
from routes.ai_enhanced import ai_bp

def register_blueprints(app):
    """注册所有蓝图"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(ai_bp)
    print("Routes registered (with Enhanced AI module)")
    print("  - AI Chat: /api/ai/chat")
    print("  - AI Assistant: /api/ai/assistant")
    print("  - AI Assistant Stream: /api/ai/assistant/stream")
    print("  - AI Generate Notification: /api/ai/generate-notification")
    print("  - Knowledge Base Search: /api/ai/knowledge-base/search")
    print("  - Knowledge Base Documents: /api/ai/knowledge-base/documents")
    print("  - Knowledge Base Reload: /api/ai/knowledge-base/reload")
    print("  - AI Health Check: /api/ai/health")
