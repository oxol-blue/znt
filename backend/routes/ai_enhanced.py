# -*- coding: utf-8 -*-
"""
增强版 AI 服务路由
集成知识库 RAG 和数据库查询功能
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
from utils import login_required, db
from services.enhanced_ai_service import enhanced_deepseek_service
from services.rag_service import knowledge_base
from services.db_tools import db_tools
from services.conversation_state import conversation_manager
import json

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """增强版 AI 聊天接口 - 集成知识库和数据库"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'code': 400, 'message': '消息不能为空'}), 400
    
    user_message = data.get('message', '').strip()
    user_id = request.current_user.get('user_id')
    user_role = request.current_user.get('role', 'student')
    
    if not user_message:
        return jsonify({'code': 400, 'message': '消息不能为空'}), 400
    
    try:
        # 使用增强版AI服务
        result = enhanced_deepseek_service.campus_assistant(
            user_message, user_id, user_role
        )
        
        if result.get('success'):
            response_text = result.get('response', '')
            
            # 添加操作结果信息
            actions = result.get('actions', [])
            if actions:
                for action in actions:
                    if action.get('success'):
                        response_text += f"\n\n✅ {action.get('message', '操作成功')}"
                    elif not action.get('needs_more_info'):
                        response_text += f"\n\n❌ {action.get('message', '操作失败')}"
            
            return jsonify({
                'code': 200,
                'message': '成功',
                'data': {
                    'response': response_text,
                    'role': 'assistant',
                    'source': 'ai_enhanced',
                    'context_used': result.get('context_used', False),
                    'intent': result.get('intent', {})
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': result.get('response', 'AI服务错误')
            })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'处理请求时出错: {str(e)}'
        })


@ai_bp.route('/assistant', methods=['POST'])
@login_required
def campus_assistant():
    """校园助手专用接口 - 支持智能查询和操作"""
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({'code': 400, 'message': '问题不能为空'}), 400
    
    question = data.get('question', '').strip()
    user_id = request.current_user.get('user_id')
    user_role = request.current_user.get('role', 'student')
    
    # 预设的常见问题快速回复
    quick_replies = {
        '图书馆开放时间': '图书馆开放时间为每天 08:00 - 22:00，节假日可能调整，请关注通知。',
        '怎么借书': '1. 在图书馆页面搜索图书 2. 点击"借阅"按钮 3. 确认借阅信息 4. 到图书馆取书',
        '怎么预约场地': '1. 进入场地预约页面 2. 选择场地类型和日期 3. 选择时间段 4. 填写用途并提交',
        '忘记密码': '请联系管理员重置密码，或发送邮件至 admin@campus.edu',
        '系统怎么用': '本系统包含图书馆、任务管理、场地预约、消息通知四大模块，可通过侧边栏切换。'
    }
    
    # 检查是否有快速回复
    for key, value in quick_replies.items():
        if key in question:
            return jsonify({
                'code': 200,
                'message': '成功',
                'data': {
                    'response': value,
                    'source': 'quick_reply'
                }
            })
    
    # 调用增强版 AI
    try:
        result = enhanced_deepseek_service.campus_assistant(
            question, user_id, user_role
        )
        
        if result.get('success'):
            response_text = result.get('response', '')
            
            # 添加操作结果
            actions = result.get('actions', [])
            if actions:
                for action in actions:
                    if action.get('success'):
                        response_text += f"\n\n✅ {action.get('message', '操作成功')}"
                    elif not action.get('needs_more_info'):
                        response_text += f"\n\n❌ {action.get('message', '操作失败')}"
            
            return jsonify({
                'code': 200,
                'message': '成功',
                'data': {
                    'response': response_text,
                    'source': 'ai_enhanced',
                    'context_used': result.get('context_used', False),
                    'intent': result.get('intent', {})
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': result.get('response', 'AI服务错误')
            })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'处理请求时出错: {str(e)}'
        })


@ai_bp.route('/assistant/stream', methods=['POST', 'OPTIONS'])
@login_required
def campus_assistant_stream():
    """校园助手流式接口 - SSE"""
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        response = jsonify({'code': 200, 'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({'code': 400, 'message': '问题不能为空'}), 400
    
    question = data.get('question', '').strip()
    context = data.get('context', [])  # 获取对话上下文
    user_id = request.current_user.get('user_id')
    user_role = request.current_user.get('role', 'student')
    print(f"[AI_STREAM] 用户ID: {user_id}, 角色: {user_role}, 上下文长度: {len(context)}")
    
    # 先分析意图
    intent = enhanced_deepseek_service._analyze_intent(question)
    print(f"[AI_STREAM] 意图: {intent}")
    
    # 【关键修复】智能判断是否需要清除状态
    is_collecting = conversation_manager.is_collecting(user_id)
    intent_action = intent.get('action')
    
    # 只有在用户发起全新操作意图时才清除
    # 逃逸机制已在 enhanced_ai_service.py 的 campus_assistant_stream 中实现
    if not is_collecting:
        if intent_action in ['create_reservation', 'borrow_book', 'publish_notification', 'create_task']:
            conversation_manager.clear_state(user_id)
            print(f"[AI_STREAM] 清除旧对话状态（新意图: {intent_action}）")
    else:
        print(f"[AI_STREAM] 保持对话状态（正在收集参数）")
    
    # 清除之前的待执行操作（避免污染）
    if intent.get('category') in ['borrow', 'book', 'reservation', 'notification', 'task'] and not intent.get('action'):
        # 纯查询意图，确保没有残留的pending action
        print(f"[AI_STREAM] 纯查询意图，确保状态干净")
    
    kb_context = knowledge_base.get_relevant_context(question)
    
    db_data = None
    data_source = None
    raw_books = None  # 原始图书数据
    if intent.get('needs_db_query'):
        print(f"[AI_STREAM] 开始查询数据库...")
        db_data = enhanced_deepseek_service._query_database(intent, user_id, user_role)
        print(f"[AI_STREAM] 数据库结果: {db_data[:100] if db_data else 'None'}...")
        if db_data:
            data_source = 'database'
            # 如果是查询图书，提取原始图书数据
            if intent.get('category') == 'book' or intent.get('action') == 'borrow_book':
                from services.db_tools import db_tools
                keyword = intent.get('params', {}).get('book_title', '')
                # 如果没有关键词，查询所有可借图书（热门推荐）
                if not keyword:
                    raw_books = db_tools.query_books(keyword="", limit=10)
                    # 只保留有库存的
                    raw_books = [b for b in raw_books if b.get("available", 0) > 0]
                else:
                    raw_books = db_tools.query_books(keyword=keyword, limit=5)
    elif kb_context:
        data_source = 'knowledge_base'
    
    def generate():
        try:
            # 发送意图识别结果
            yield f"data: {json.dumps({'type': 'intent', 'data': intent}, ensure_ascii=False)}\n\n"
            
            # 发送图书原始数据（仅在用户明确要借书时，用于确认按钮）
            if raw_books and intent.get('action') == 'borrow_book':
                yield f"data: {json.dumps({'type': 'books', 'data': raw_books}, ensure_ascii=False)}\n\n"
            
            # 发送数据库数据标记
            if db_data:
                yield f"data: {json.dumps({'type': 'db_data', 'data': True}, ensure_ascii=False)}\n\n"
            
            # 发送数据来源
            if data_source:
                yield f"data: {json.dumps({'type': 'data_source', 'data': data_source}, ensure_ascii=False)}\n\n"
            
            # 流式调用AI
            print(f"[AI_STREAM] 开始流式生成，db_data长度: {len(db_data) if db_data else 0}")
            print(f"[AI_STREAM] raw_books数量: {len(raw_books) if raw_books else 0}")
            chunk_count = 0
            pending_action_sent = False
            for chunk in enhanced_deepseek_service.campus_assistant_stream(
                question, user_id, user_role, db_data, context
            ):
                chunk_count += 1
                # 检查是否是 pending_action 标记
                if chunk.startswith('__PENDING_ACTION__:'):
                    try:
                        action_data = json.loads(chunk[19:])  # 去掉前缀
                        yield f"data: {json.dumps({'type': 'pending_action', 'data': action_data}, ensure_ascii=False)}\n\n"
                        pending_action_sent = True
                        print(f"[AI_STREAM] 发送 pending_action: {action_data}")
                    except json.JSONDecodeError:
                        print(f"[AI_STREAM] pending_action 解析失败: {chunk}")
                    continue
                
                if chunk_count <= 5:  # 只打印前5个chunk
                    print(f"[AI_STREAM] chunk {chunk_count}: {chunk[:50] if len(chunk) > 50 else chunk}...")
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"
            
            yield f"data: [DONE]\n\n"
        except Exception as e:
            print(f"[AI_STREAM] 生成器错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"
            yield f"data: [DONE]\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@ai_bp.route('/execute-action', methods=['POST'])
@login_required
def execute_action():
    """执行操作接口（如确认借书）"""
    data = request.get_json()
    
    action = data.get('action')
    params = data.get('params', {})
    user_id = request.current_user.get('user_id')
    user_role = request.current_user.get('role', 'student')
    
    print(f"[EXECUTE_ACTION] 执行操作: {action}, 用户: {user_id}, 参数: {params}")
    
    try:
        if action == 'borrow_book':
            if user_role != 'student':
                return jsonify({'code': 403, 'message': '只有学生可以借书'}), 403
            
            book_id = params.get('book_id')
            if not book_id:
                return jsonify({'code': 400, 'message': '缺少图书ID'}), 400
            
            # 执行借阅
            result = db_tools.create_borrow(user_id=user_id, book_id=book_id)
            return jsonify({
                'code': 200 if result.get('success') else 400,
                'message': result.get('message', '操作完成'),
                'data': result
            })
        
        elif action == 'create_reservation':
            if user_role != 'student':
                return jsonify({'code': 403, 'message': '只有学生可以预约场地'}), 403
            
            venue_id = params.get('venue_id')
            date = params.get('date')
            start_time = params.get('start_time')
            end_time = params.get('end_time')
            purpose = params.get('purpose', '学习')
            
            # 验证必要参数
            missing = []
            if not venue_id: missing.append('场地ID')
            if not date: missing.append('日期')
            if not start_time: missing.append('开始时间')
            if not end_time: missing.append('结束时间')
            
            if missing:
                missing_str = '、'.join(missing)
                return jsonify({
                    'code': 400, 
                    'message': f'缺少必要的预约参数：{missing_str}'
                }), 400
            
            # 执行预约
            result = db_tools.create_reservation(
                user_id=user_id,
                venue_id=venue_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                purpose=purpose
            )
            return jsonify({
                'code': 200 if result.get('success') else 400,
                'message': result.get('message', '操作完成'),
                'data': result
            })
        
        else:
            return jsonify({'code': 400, 'message': '未知的操作类型'}), 400
    
    except Exception as e:
        print(f"[EXECUTE_ACTION] 执行失败: {e}")
        return jsonify({'code': 500, 'message': f'执行失败: {str(e)}'}), 500


@ai_bp.route('/generate-notification', methods=['POST'])
@login_required
def generate_notification():
    """AI 辅助生成通知 - 支持一键发布"""
    data = request.get_json()
    
    title = data.get('title', '')
    content_type = data.get('type', 'announcement')
    target = data.get('target', '全体师生')
    auto_publish = data.get('auto_publish', False)  # 是否直接发布
    
    if not title:
        return jsonify({'code': 400, 'message': '标题不能为空'}), 400
    
    # 生成通知内容
    content = enhanced_deepseek_service.generate_notification(title, content_type, target)
    
    response_data = {
        'code': 200,
        'message': '生成成功',
        'data': {
            'title': title,
            'content': content,
            'type': content_type,
            'target': target
        }
    }
    
    # 如果请求自动发布
    if auto_publish:
        user_role = request.current_user.get('role', 'student')
        if user_role not in ['teacher', 'admin']:
            response_data['data']['publish_warning'] = '只有教师或管理员可以发布通知'
        else:
            user_id = request.current_user.get('user_id')
            from services.db_tools import db_tools
            result = db_tools.publish_notification(
                sender_id=user_id,
                title=title,
                content=content,
                target_type="all"
            )
            response_data['data']['published'] = result.get('success', False)
            response_data['data']['publish_message'] = result.get('message', '')
    
    return jsonify(response_data)


@ai_bp.route('/knowledge-base/search', methods=['POST'])
@login_required
def search_knowledge_base():
    """搜索知识库"""
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 5)
    
    if not query:
        return jsonify({'code': 400, 'message': '查询内容不能为空'}), 400
    
    try:
        results = knowledge_base.search(query, top_k=top_k)
        return jsonify({
            'code': 200,
            'message': '搜索成功',
            'data': {
                'query': query,
                'results': results
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'搜索失败: {str(e)}'
        })


@ai_bp.route('/knowledge-base/documents', methods=['GET'])
@login_required
def list_knowledge_documents():
    """获取知识库文档列表"""
    try:
        documents = knowledge_base.list_documents()
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'documents': documents,
                'count': len(documents)
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}'
        })


@ai_bp.route('/knowledge-base/reload', methods=['POST'])
@login_required
def reload_knowledge_base():
    """重新加载知识库"""
    user_role = request.current_user.get('role', 'student')
    if user_role not in ['teacher', 'admin']:
        return jsonify({'code': 403, 'message': '无权限执行此操作'}), 403
    
    try:
        # 清空并重新加载
        knowledge_base.clear()
        result = knowledge_base.load_all_documents()
        
        return jsonify({
            'code': 200,
            'message': '知识库重新加载成功',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'重新加载失败: {str(e)}'
        })


@ai_bp.route('/test-db', methods=['GET'])
@login_required
def test_db_query():
    """测试数据库查询 - 用于调试"""
    try:
        from services.db_tools import db_tools
        user_id = request.current_user.get('user_id')
        
        # 查询借阅记录
        borrows = db_tools.query_user_borrows(user_id)
        
        return jsonify({
            'code': 200,
            'data': {
                'user_id': user_id,
                'borrows': borrows
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'查询失败: {str(e)}'
        })


@ai_bp.route('/health', methods=['GET'])
def ai_health_check():
    """AI 服务健康检查"""
    try:
        # 检查 API 可用性
        from services.ai_service import deepseek_service
        response = deepseek_service.simple_chat('你好', '你是一个测试助手，请回复"服务正常"')
        is_healthy = '服务正常' in response or len(response) > 0
        
        # 检查知识库状态
        kb_docs = knowledge_base.list_documents()
        
        return jsonify({
            'code': 200,
            'data': {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'model': enhanced_deepseek_service.model,
                'knowledge_base': {
                    'documents': len(kb_docs),
                    'files': kb_docs
                },
                'response': response[:50] + '...' if len(response) > 50 else response
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'AI服务异常: {str(e)}',
            'data': {
                'status': 'error'
            }
        })
