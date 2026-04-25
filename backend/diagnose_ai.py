# -*- coding: utf-8 -*-
"""
AI服务诊断脚本
"""
import sys
sys.path.insert(0, 'C:/Users/hcb52/Desktop/znn/backend')

def check_imports():
    """检查所有导入"""
    print("=" * 50)
    print("检查导入...")
    print("=" * 50)
    
    try:
        from services.ai_service import deepseek_service
        print("[OK] ai_service 导入成功")
    except Exception as e:
        print(f"[FAIL] ai_service 导入失败: {e}")
    
    try:
        from services.enhanced_ai_service import enhanced_deepseek_service
        print("[OK] enhanced_ai_service 导入成功")
    except Exception as e:
        print(f"[FAIL] enhanced_ai_service 导入失败: {e}")
    
    try:
        from services.rag_service import knowledge_base
        print("[OK] rag_service 导入成功")
    except Exception as e:
        print(f"[FAIL] rag_service 导入失败: {e}")
    
    try:
        from services.db_tools import db_tools
        print("[OK] db_tools 导入成功")
    except Exception as e:
        print(f"[FAIL] db_tools 导入失败: {e}")
    
    try:
        from routes.ai_enhanced import ai_bp
        print("[OK] ai_enhanced 路由导入成功")
        print(f"   路由URL前缀: {ai_bp.url_prefix}")
    except Exception as e:
        print(f"[FAIL] ai_enhanced 路由导入失败: {e}")

def check_routes():
    """检查Flask路由"""
    print("\n" + "=" * 50)
    print("检查Flask路由...")
    print("=" * 50)
    
    try:
        from app import app
        with app.test_client() as client:
            # 测试健康检查
            response = client.get('/api/health')
            print(f"[OK] /api/health 状态: {response.status_code}")
            
            # 测试AI路由
            response = client.get('/api/ai/health')
            print(f"[OK] /api/ai/health 状态: {response.status_code}")
            
            print("\n所有路由列表:")
            for rule in app.url_map.iter_rules():
                if 'api' in str(rule):
                    print(f"  {rule.methods} {rule.rule}")
    except Exception as e:
        print(f"[FAIL] 路由检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_imports()
    check_routes()
    
    print("\n" + "=" * 50)
    print("诊断完成")
    print("=" * 50)
    print("\n请按 Enter 键退出...")
    input()
