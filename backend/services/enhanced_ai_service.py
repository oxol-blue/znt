# -*- coding: utf-8 -*-
"""
增强版 DeepSeek AI 服务模块
集成知识库 RAG 和数据库工具
"""
import json
import requests
from typing import List, Dict, Optional, Generator, Callable
from datetime import datetime
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, DEEPSEEK_MODEL
from services.rag_service import knowledge_base
from services.db_tools import db_tools


class EnhancedDeepSeekService:
    """增强版 DeepSeek AI 服务类"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_base = DEEPSEEK_API_BASE
        self.model = DEEPSEEK_MODEL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict:
        """发送聊天请求"""
        url = f"{self.api_base}/chat/completions"
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'stream': stream
        }
        
        if max_tokens:
            data['max_tokens'] = max_tokens
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': True,
                'message': f'API请求失败: {str(e)}'
            }
    
    def simple_chat(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """简单聊天接口"""
        messages = []
        
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        response = self.chat(messages)
        
        if 'error' in response:
            return f"抱歉，AI服务暂时不可用: {response.get('message', '未知错误')}"
        
        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            return f"解析响应失败: {str(e)}"
    
    def campus_assistant(self, user_message: str, user_id: int, user_role: str = 'student') -> Dict:
        """
        增强版校园智能助手
        集成知识库和数据库查询
        """
        # 1. 首先判断用户意图
        intent = self._analyze_intent(user_message)
        
        # 2. 根据意图获取相关信息
        context_parts = []
        actions = []
        
        # 获取知识库相关内容
        kb_context = knowledge_base.get_relevant_context(user_message)
        if kb_context:
            context_parts.append(f"【知识库信息】\n{kb_context}")
        
        # 根据意图查询数据库
        db_data = None
        if intent.get("needs_db_query"):
            print(f"[DEBUG] 需要查询数据库，意图: {intent.get('category')}, 用户ID: {user_id}")
            db_data = self._query_database(intent, user_id, user_role)
            print(f"[DEBUG] 数据库查询结果: {db_data[:200] if db_data else '无数据'}...")
            if db_data:
                context_parts.append(f"【数据库信息】\n{db_data}")
        
        # 检查是否需要执行操作
        if intent.get("action"):
            action_result = self._execute_action(
                intent["action"], 
                intent.get("params", {}),
                user_id, 
                user_role
            )
            actions.append(action_result)
        
        # 3. 构建系统提示词 - 无论是否有数据都使用AI生成回复
        system_prompt = f"""你是智慧校园AI助手，当前为已登录的{user_role}用户提供服务。

当前时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}

【关键指令 - 必须遵守】
1. 用户已登录系统，你已获取其个人数据查询权限
2. 当系统提供【数据库信息】时，这是用户的真实数据，你必须基于这些数据直接回答
3. 绝对禁止说"无法访问""需要到其他系统查询"或"请提供学号"
4. 直接基于提供的数据生成友好、自然的回复
5. 如果数据为空，告知用户"暂无相关记录"

【严禁编造数据 - 重要】
- 你必须严格基于系统提供的【数据库信息】回答，禁止编造任何图书记录
- 如果系统提供的数据为空或"暂无图书记录"，你必须如实告知用户，不能自己编造推荐
- 绝对禁止推荐《三体》《百年孤独》等数据库中不存在的书籍
- 你只能推荐系统数据查询结果中真实存在的图书

你的职责：
1. 解答校园相关问题
2. 基于提供的数据回答用户问题（禁止编造）
3. 协助完成预约、任务等操作
4. 保持友好、专业、耐心的态度

{"已执行操作：" + json.dumps(actions, ensure_ascii=False) if actions else ""}
"""
        
        # 4. 构建完整消息
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if context_parts:
            context_content = "\n\n".join(context_parts)
            if db_data:
                context_content += "\n\n【重要】以上是你的真实数据，请直接基于这些数据回答用户问题，不要询问其他信息。"
            messages.append({
                "role": "system", 
                "content": context_content
            })
        
        messages.append({"role": "user", "content": user_message})
        
        # 6. 调用AI - 有数据时使用更低temperature让AI更听话
        temp = 0.3 if db_data else 0.7
        response = self.chat(messages, temperature=temp)
        
        if 'error' in response:
            return {
                "success": False,
                "response": f"抱歉，AI服务暂时不可用: {response.get('message', '未知错误')}",
                "actions": actions
            }
        
        try:
            ai_response = response['choices'][0]['message']['content']
            return {
                "success": True,
                "response": ai_response,
                "actions": actions,
                "intent": intent,
                "context_used": len(context_parts) > 0
            }
        except (KeyError, IndexError) as e:
            return {
                "success": False,
                "response": f"解析响应失败: {str(e)}",
                "actions": actions
            }
    
    def campus_assistant_stream(self, user_message: str, user_id: int, user_role: str = 'student', db_data: str = None, context: list = None):
        """
        流式校园智能助手
        返回生成器，逐字输出AI回复
        """
        # 构建消息
        intent = self._analyze_intent(user_message)
        context_parts = []
        
        # 获取知识库内容
        kb_context = knowledge_base.get_relevant_context(user_message)
        if kb_context:
            context_parts.append(f"【知识库信息】\n{kb_context}")
        
        if db_data:
            context_parts.append(f"【数据库信息】\n{db_data}")
        
        system_prompt = f"""你是智慧校园AI助手，当前为已登录的{user_role}用户提供服务。

当前时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}

【关键指令 - 必须遵守】
1. 用户已登录系统，你已获取其个人数据查询权限
2. 当系统提供【数据库信息】时，这是用户的真实数据，你必须基于这些数据直接回答
3. 绝对禁止说"无法访问""需要到其他系统查询"或"请提供学号"
4. 直接基于提供的数据生成友好、自然的回复
5. 如果数据为空，告知用户"暂无相关记录"

【严禁编造数据 - 重要】
- 你必须严格基于系统提供的【数据库信息】回答，禁止编造任何图书记录
- 如果系统提供的数据为空或"暂无图书记录"，你必须如实告知用户，不能自己编造推荐
- 绝对禁止推荐《三体》《百年孤独》等数据库中不存在的书籍
- 你只能推荐系统数据查询结果中真实存在的图书

【借书流程】当用户想借书时：
1. 系统已查询到图书信息，会在【数据库信息】中提供
2. 向用户展示书名、可借数量、馆藏位置（基于真实数据，禁止编造）
3. 询问用户"是否确认借阅这本书？"
4. 用户确认后，系统会办理借阅手续
5. 不要说自己无法获取库存信息，数据已经在【数据库信息】中

你的职责：
1. 解答校园相关问题
2. 基于提供的数据回答用户问题（禁止编造）
3. 记住之前的对话内容，保持上下文连贯
4. 保持友好、专业、耐心的态度
"""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if context_parts:
            context_content = "\n\n".join(context_parts)
            if db_data:
                context_content += "\n\n【重要】以上是你的真实数据，请直接基于这些数据回答用户问题，不要询问其他信息。"
            messages.append({
                "role": "system", 
                "content": context_content
            })
        
        # 添加上下文历史
        if context and len(context) > 0:
            for msg in context:
                if msg.get('content'):  # 确保消息不为空
                    messages.append({
                        "role": msg.get('role', 'user'),
                        "content": msg['content']
                    })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 流式调用AI
        temp = 0.3 if db_data else 0.7
        url = f"{self.api_base}/chat/completions"
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temp,
            'stream': True
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=data,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n\n[生成回复时出错: {str(e)}]"
    
    def _analyze_intent(self, message: str) -> Dict:
        """使用AI分析用户意图"""
        intent = {
            "category": "general",
            "needs_db_query": False,
            "action": None,
            "params": {},
            "original_message": message
        }
        
        # 使用AI进行意图识别
        prompt = f"""分析用户意图，返回JSON格式：
{{
  "category": "类别(borrow/book/reservation/venue/notification/task/profile/general)",
  "needs_db_query": true/false,
  "action": "操作类型(publish_notification/create_reservation/borrow_book/complete_task/null)",
  "params": {{}}
}}

用户消息："{message}"

规则：
- "我借了哪些书" -> category: "borrow", needs_db_query: true
- "帮我借《深度学习》" -> category: "book", action: "borrow_book", params: {{"book_title": "深度学习"}}
- "查一下有没有Python书" -> category: "book", needs_db_query: true
- "我的预约" -> category: "reservation", needs_db_query: true
- "发布通知" -> category: "general", action: "publish_notification"
- "确认/可以/好的/是的" -> category: "general", action: "confirm", needs_db_query: false (表示用户确认执行之前的操作)
- "取消/不要/算了" -> category: "general", action: "cancel", needs_db_query: false
- "我想借书"（没有具体书名） -> category: "book", needs_db_query: true, action: null (只查询可借图书，不执行借阅)
- "我想借《xxx》"（有具体书名） -> category: "book", needs_db_query: true, action: "borrow_book", params: {{"book_title": "xxx"}}

只返回JSON，不要其他内容。"""
        
        try:
            result = self.simple_chat(prompt, "你是一个意图识别助手")
            import json
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                ai_intent = json.loads(json_match.group())
                intent.update(ai_intent)
                print(f"[DEBUG] AI意图识别: {intent}")
        except Exception as e:
            print(f"[DEBUG] AI意图识别失败，使用关键词匹配: {e}")
            # 降级到关键词匹配
            return self._analyze_intent_by_keywords(message)
        
        return intent
    
    def _analyze_intent_by_keywords(self, message: str) -> Dict:
        """关键词匹配作为降级方案"""
        message_lower = message.lower()
        intent = {
            "category": "general",
            "needs_db_query": False,
            "action": None,
            "params": {},
            "original_message": message
        }
        
        query_keywords = {
            "borrow": ["借书", "借阅", "借了", "在借", "我借了", "我借了什么"],
            "book": ["图书", "书籍", "找书", "查书", "有没有", "书"],
            "reservation": ["预约", "预定", "预订"],
            "venue": ["场地", "教室", "实验室", "图书馆座位"],
            "notification": ["通知", "消息", "公告", "未读"],
            "task": ["任务", "作业", "待办"],
            "profile": ["我的信息", "个人信息", "资料", "我的账号"]
        }
        
        for category, keywords in query_keywords.items():
            if any(kw in message_lower for kw in keywords):
                intent["category"] = category
                intent["needs_db_query"] = True
                break
        
        action_keywords = {
            "publish_notification": ["发布通知", "发通知", "发布公告", "发送通知"],
            "create_reservation": ["预约场地", "预定场地", "我要预约", "帮我预约"],
            "complete_task": ["完成任务", "做完任务", "提交任务"],
            "borrow_book": ["帮我借", "我要借", "办理借阅"]  # 移除了"借书"、"我想借"，这些改为查询
        }
        
        # 特殊处理："我想借书"但没指定书名 -> 查询可借图书
        if "我想借书" in message or ("借书" in message and "《" not in message and "书" in message):
            # 检查是否有具体书名
            import re
            has_book_title = re.search(r'《(.+?)》', message) or re.search(r'(?:借|查|找)(?:一?[本个]?)[书]?["\'](.+?)["\']', message)
            if not has_book_title:
                intent["category"] = "book"
                intent["needs_db_query"] = True
                intent["action"] = None  # 不执行借书操作，只查询
        
        for action, keywords in action_keywords.items():
            if any(kw in message for kw in keywords):
                intent["action"] = action
                intent["params"] = self._extract_params(message, action)
                break
        
        return intent
    
    def _extract_params(self, message: str, action: str) -> Dict:
        """提取操作参数"""
        import re
        params = {}
        
        if action == "publish_notification":
            # 尝试提取标题（匹配中文引号""或英文引号"）
            title_match = re.search(r'["""](.+?)["""]', message)
            if title_match:
                params["title"] = title_match.group(1)
            else:
                # 提取"关于...的通知"或标题后的内容
                title_match = re.search(r'关于(.+?)(?:的)?通知', message)
                if title_match:
                    params["title"] = f"关于{title_match.group(1)}的通知"
            
            # 提取内容
            content_match = re.search(r'内容[:：](.+?)(?:$|发送给|面向)', message, re.DOTALL)
            if content_match:
                params["content"] = content_match.group(1).strip()
        
        elif action == "create_reservation":
            # 提取日期
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日|明天|后天|今天)', message)
            if date_match:
                params["date"] = date_match.group(1)
            
            # 提取时间
            time_match = re.search(r'(\d{1,2}[：:]\d{2}).{0,5}(\d{1,2}[：:]\d{2})', message)
            if time_match:
                params["start_time"] = time_match.group(1).replace("：", ":")
                params["end_time"] = time_match.group(2).replace("：", ":")
            
            # 提取场地类型
            venue_types = {
                "图书馆": "library",
                "实验室": "lab",
                "教室": "classroom",
                "会议室": "meeting_room"
            }
            for cn, en in venue_types.items():
                if cn in message:
                    params["venue_type"] = en
                    break
        
        elif action == "borrow_book":
            # 提取书名（匹配书名号《》或引号）
            title_match = re.search(r'《(.+?)》', message)
            if title_match:
                params["book_title"] = title_match.group(1)
            else:
                # 尝试提取"借/查/找 + 书名"后面的内容
                title_match = re.search(r'(?:借|查|找)(?:一?[本个]?)[书]?(.+?)(?:的?)$', message)
                if title_match:
                    params["book_title"] = title_match.group(1).strip()
        
        return params
    
    def _query_database(self, intent: Dict, user_id: int, user_role: str) -> str:
        """根据意图查询数据库"""
        category = intent.get("category", "")
        action = intent.get("action", "")
        params = intent.get("params", {})
        print(f"[DB_QUERY] 查询类别: {category}, 操作: {action}, 用户ID: {user_id}")
        
        if category == "borrow":
            records = db_tools.query_user_borrows(user_id)
            print(f"[DB_QUERY] 借阅记录: {len(records)} 条")
            if any("error" in r for r in records):
                return f"查询出错：{records[0].get('error', '未知错误')}"
            return f"您的借阅记录（共{len(records)}条）：\n{json.dumps(records, ensure_ascii=False, indent=2)}"
        
        elif category == "book" or action == "borrow_book":
            # 提取关键词 - 优先从params中获取
            keyword = params.get("book_title", "")
            if not keyword:
                import re
                keywords = re.findall(r'《(.+?)》|"(.+?)"', intent.get("original_message", ""))
                keyword = keywords[0][0] if keywords else ""
            
            print(f"[DB_QUERY] 查询图书: {keyword if keyword else '全部热门图书'}")
            # 如果没有关键词，查询所有可借图书（热门推荐）
            if not keyword:
                books = db_tools.query_books(keyword="", limit=10)
                # 只保留有库存的图书
                books = [b for b in books if b.get("available", 0) > 0]
                print(f"[DB_QUERY] 可借图书: {len(books)} 本")
                if not books:
                    return "【数据库信息】\n当前暂无图书记录或所有图书已借完"
                return f"【数据库信息】\n当前可借图书（共{len(books)}本）：\n{json.dumps(books, ensure_ascii=False, indent=2)}"
            else:
                books = db_tools.query_books(keyword=keyword, limit=5)
                print(f"[DB_QUERY] 查询结果: {len(books)} 本")
                if any("error" in b for b in books):
                    return f"查询出错：{books[0].get('error', '未知错误')}"
                return f"图书查询结果（共{len(books)}本）：\n{json.dumps(books, ensure_ascii=False, indent=2)}"
        
        elif category == "reservation":
            reservations = db_tools.query_user_reservations(user_id)
            if any("error" in r for r in reservations):
                return f"查询出错：{reservations[0].get('error', '未知错误')}"
            return f"您的预约记录（共{len(reservations)}条）：\n{json.dumps(reservations, ensure_ascii=False, indent=2)}"
        
        elif category == "venue":
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")
            venues = db_tools.query_venues(date=date)
            if any("error" in v for v in venues):
                return f"查询出错：{venues[0].get('error', '未知错误')}"
            return f"今日可用场地（共{len(venues)}个）：\n{json.dumps(venues[:5], ensure_ascii=False, indent=2)}"
        
        elif category == "notification":
            notifications = db_tools.query_notifications(user_id, user_role, unread_only=True)
            if any("error" in n for n in notifications):
                return f"查询出错：{notifications[0].get('error', '未知错误')}"
            return f"您的未读通知（共{len(notifications)}条）：\n{json.dumps(notifications, ensure_ascii=False, indent=2)}"
        
        elif category == "task":
            tasks = db_tools.query_tasks(user_id, user_role)
            if any("error" in t for t in tasks):
                return f"查询出错：{tasks[0].get('error', '未知错误')}"
            return f"您的任务列表（共{len(tasks)}条）：\n{json.dumps(tasks, ensure_ascii=False, indent=2)}"
        
        return ""
    
    def _execute_action(self, action: str, params: Dict, user_id: int, user_role: str) -> Dict:
        """执行操作"""
        result = {"action": action, "success": False}
        
        if action == "publish_notification":
            if user_role not in ['teacher', 'admin']:
                result["message"] = "只有教师或管理员可以发布通知"
                return result
            
            title = params.get("title", "")
            content = params.get("content", "")
            
            if not title:
                result["message"] = "通知标题不能为空"
                return result
            
            # 如果没有提供内容，让AI生成
            if not content:
                content = self.generate_notification(title, "announcement", "全体师生")
            
            db_result = db_tools.publish_notification(
                sender_id=user_id,
                title=title,
                content=content,
                target_type="all"
            )
            result.update(db_result)
        
        elif action == "create_reservation":
            if user_role != 'student':
                result["message"] = "只有学生可以预约场地"
                return result
            
            # 这里需要更多参数，暂时返回提示
            result["message"] = "请提供完整的预约信息：场地、日期、时间段和用途"
            result["needs_more_info"] = True
        
        elif action == "borrow_book":
            if user_role != 'student':
                result["message"] = "只有学生可以借书"
                return result
            
            book_title = params.get("book_title", "")
            if not book_title:
                result["message"] = "请提供要借阅的书名"
                return result
            
            # 查询图书
            books = db_tools.query_books(keyword=book_title, limit=5)
            if not books or len(books) == 0:
                result["message"] = f"未找到《{book_title}》相关图书"
                return result
            
            if any("error" in b for b in books):
                result["message"] = "查询图书失败"
                return result
            
            # 找第一本可借的书
            available_book = None
            for book in books:
                if book.get("available", 0) > 0:
                    available_book = book
                    break
            
            if not available_book:
                result["message"] = f"《{book_title}》暂时没有可借的库存"
                result["books"] = books  # 返回相关书籍供用户选择
                return result
            
            # 执行借阅操作
            borrow_result = db_tools.create_borrow(
                user_id=user_id,
                book_id=available_book["id"]
            )
            
            if borrow_result.get("success"):
                result["success"] = True
                result["message"] = f"成功借阅《{available_book['title']}》，请在30天内归还。书的位置：{available_book.get('location', '请咨询管理员')}"
            else:
                result["message"] = borrow_result.get("message", "借阅失败")
        
        return result
    
    def generate_notification(self, title: str, content_type: str, target: str) -> str:
        """辅助生成通知内容"""
        prompt = f"""请帮我撰写一份校园通知：

标题主题：{title}
通知类型：{content_type}
目标受众：{target}

要求：
1. 格式规范、语言得体
2. 内容清晰、重点突出
3. 包含必要的要素（时间、地点、要求等）
4. 语气正式但不失亲和力
5. 字数控制在200-400字"""

        return self.simple_chat(prompt)
    
    def intelligent_assistant(self, message: str, user_id: int, user_role: str) -> str:
        """
        智能助手统一入口
        返回格式化的回复
        """
        result = self.campus_assistant(message, user_id, user_role)
        
        if not result.get("success"):
            return result.get("response", "抱歉，处理您的请求时出错了")
        
        response = result.get("response", "")
        actions = result.get("actions", [])
        
        # 如果有执行操作，添加操作结果信息
        if actions:
            for action in actions:
                if action.get("success"):
                    response += f"\n\n✅ {action.get('message', '操作成功')}"
                else:
                    response += f"\n\n❌ {action.get('message', '操作失败')}"
        
        return response


# 全局服务实例
enhanced_deepseek_service = EnhancedDeepSeekService()
