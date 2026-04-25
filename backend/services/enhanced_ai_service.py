# -*- coding: utf-8 -*-
"""
增强版 DeepSeek AI 服务模块
集成知识库 RAG 和数据库工具
"""
import json
import re
import requests
from typing import List, Dict, Optional, Generator, Callable
from datetime import datetime, timedelta
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, DEEPSEEK_MODEL
from services.rag_service import knowledge_base
from services.db_tools import db_tools
from services.conversation_state import conversation_manager


# 日期时间解析工具函数
# 中文数字转阿拉伯数字映射
CHINESE_DIGITS = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
    '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24
}

def chinese_to_arabic(chinese_str: str) -> int:
    """
    将中文数字转换为阿拉伯数字
    支持：零到二十四
    """
    chinese_str = chinese_str.strip()
    if chinese_str in CHINESE_DIGITS:
        return CHINESE_DIGITS[chinese_str]
    
    # 处理 "十一"、"十二"、"二十" 等组合
    if '十' in chinese_str:
        parts = chinese_str.split('十')
        if len(parts) == 2:
            if parts[0] == '':  # "十"、"十一"
                tens = 1
            else:
                tens = CHINESE_DIGITS.get(parts[0], 0)
            if parts[1] == '':  # "十"
                ones = 0
            else:
                ones = CHINESE_DIGITS.get(parts[1], 0)
            return tens * 10 + ones
    
    return 0


def parse_date(date_str: str) -> Optional[str]:
    """解析日期字符串，返回YYYY-MM-DD格式"""
    from datetime import datetime, timedelta
    import re
    
    today = datetime.now()
    
    # 相对日期
    if date_str == '今天':
        return today.strftime('%Y-%m-%d')
    elif date_str == '明天':
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_str == '后天':
        return (today + timedelta(days=2)).strftime('%Y-%m-%d')
    
    # 绝对日期格式
    # YYYY-MM-DD 或 YYYY/MM/DD
    match = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    # MM月DD日
    match = re.match(r'(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        month, day = match.groups()
        return f"{today.year}-{int(month):02d}-{int(day):02d}"
    
    return None


def parse_time(time_str: str) -> Optional[str]:
    """解析时间字符串，返回HH:MM格式"""
    import re
    
    # 24小时制 HH:MM 或 HH：MM
    match = re.match(r'(\d{1,2})[:：](\d{2})', time_str)
    if match:
        hour, minute = match.groups()
        return f"{int(hour):02d}:{minute}"
    
    # 12小时制 上午/下午
    match = re.match(r'(上午|下午|早上|晚上)(\d{1,2})点(?:([\d]{2})分)?', time_str)
    if match:
        period, hour, minute = match.groups()
        hour = int(hour)
        minute = minute or '00'
        
        if period in ['下午', '晚上'] and hour != 12:
            hour += 12
        elif period == '上午' and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute}"
    
    # 新增：12小时制 + 中文数字（如"上午十点"）
    match = re.match(r'(上午|下午|早上|晚上)([零一二三四五六七八九十]+)点(?:([零一二三四五六七八九十]+)分)?', time_str)
    if match:
        period, hour_str, minute_str = match.groups()
        hour = chinese_to_arabic(hour_str)
        if minute_str:
            minute = chinese_to_arabic(minute_str)
            minute_str = f"{minute:02d}"
        else:
            minute_str = '00'
        
        if period in ['下午', '晚上'] and hour != 12:
            hour += 12
        elif period == '上午' and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute_str}"
    
    # 纯数字（如 "2点"）
    match = re.match(r'(\d{1,2})点', time_str)
    if match:
        hour = int(match.group(1))
        return f"{hour:02d}:00"
    
    # 新增：纯中文数字（如 "十点"）
    match = re.match(r'([零一二三四五六七八九十]+)点(?:([零一二三四五六七八九十]+)分)?', time_str)
    if match:
        hour_str = match.group(1)
        minute_str = match.group(2)
        hour = chinese_to_arabic(hour_str)
        if minute_str:
            minute = chinese_to_arabic(minute_str)
            return f"{hour:02d}:{minute:02d}"
        return f"{hour:02d}:00"
    
    return None


def extract_time_range(message: str) -> tuple:
    """提取时间范围，返回 (start_time, end_time)"""
    import re
    
    # 匹配 "X点到Y点" 或 "X:00到Y:00"
    patterns = [
        r'(\d{1,2})[:：]?(\d{2})?\s*到\s*(\d{1,2})[:：]?(\d{2})?',
        r'(\d{1,2})点(?:到|~|-)(\d{1,2})点',
        r'下午(\d{1,2})点到下午(\d{1,2})点',
        r'上午(\d{1,2})点到上午(\d{1,2})点',
        # 新增中文数字模式
        r'上午([零一二三四五六七八九十]+)点到下午([零一二三四五六七八九十]+)点',
        r'上午([零一二三四五六七八九十]+)点到上午([零一二三四五六七八九十]+)点',
        r'下午([零一二三四五六七八九十]+)点到下午([零一二三四五六七八九十]+)点',
        r'([零一二三四五六七八九十]+)点(?:到|~|-)([零一二三四五六七八九十]+)点',
        # 新增：上午/下午X点到Y点（第二个时间没有上午/下午前缀）
        r'(上午|下午)([零一二三四五六七八九十]+)点到([零一二三四五六七八九十]+)点',
        r'(上午|下午)(\d{1,2})点到(\d{1,2})点',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            groups = match.groups()
            # 检查是否是 上午/下午X点到Y点 模式（3个group，第一个是period）
            if len(groups) == 3 and groups[0] in ['上午', '下午']:
                period, start_str, end_str = groups
                # 判断是中文数字还是阿拉伯数字
                if any(c in start_str for c in '零一二三四五六七八九十'):
                    start_hour = chinese_to_arabic(start_str)
                    end_hour = chinese_to_arabic(end_str)
                else:
                    start_hour = int(start_str)
                    end_hour = int(end_str)
                
                # 转换时间
                if period == '下午' and start_hour != 12:
                    start_hour += 12
                start = f"{start_hour:02d}:00"
                
                # 结束时间假设也是同一时段（下午）
                if period == '下午' and end_hour != 12:
                    end_hour += 12
                end = f"{end_hour:02d}:00"
                return start, end
            
            # 检查是否包含中文数字
            elif any(c in groups[0] for c in '零一二三四五六七八九十'):
                # 中文数字模式
                if len(groups) >= 4 and groups[1] and any(c in groups[1] for c in '零一二三四五六七八九十\d'):  # 有分钟
                    h1_str, m1_str, h2_str, m2_str = groups[:4]
                    h1 = chinese_to_arabic(h1_str)
                    m1 = chinese_to_arabic(m1_str)
                    h2 = chinese_to_arabic(h2_str)
                    m2 = chinese_to_arabic(m2_str)
                    start = f"{h1:02d}:{m1:02d}"
                    end = f"{h2:02d}:{m2:02d}"
                else:  # 只有小时
                    h1_str, h2_str = groups[:2]
                    h1 = chinese_to_arabic(h1_str)
                    h2 = chinese_to_arabic(h2_str)
                    start = f"{h1:02d}:00"
                    end = f"{h2:02d}:00"
                return start, end
            else:
                # 阿拉伯数字模式
                if len(groups) == 4:  # 有分钟
                    h1, m1, h2, m2 = groups
                    start = f"{int(h1):02d}:{m1 or '00'}"
                    end = f"{int(h2):02d}:{m2 or '00'}"
                else:  # 只有小时
                    h1, h2 = groups[:2]
                    start = f"{int(h1):02d}:00"
                    end = f"{int(h2):02d}:00"
                return start, end
    
    return None, None


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

【数据来源约束 - 最高优先级，必须严格遵守】
1. 你只拥有以下两类信息来源：
   - 【数据库信息】：系统从数据库实时查询的用户个人数据
   - 【知识库信息】：系统从知识库文档中检索的校园相关信息

2. 严禁使用训练数据：禁止使用你预训练知识中的任何信息回答用户问题

3. 数据为空时的处理：
   - 如果【数据库信息】为空 → 回复"系统中暂无您的相关记录"
   - 如果【知识库信息】为空 → 回复"系统中暂无相关信息"
   - 如果两者都为空 → 回复"系统中暂无相关信息，无法回答您的问题"

【绝对禁止的行为】
- 严禁编造任何数据、记录、图书、人物、事件
- 严禁推荐数据库中不存在的图书
- 严禁假设、推测、生成看似合理但实际不存在的信息
- 严禁使用"比如"、"例如"来列举系统未提供的内容
- 严禁说"我可以为您推荐..."然后编造推荐内容

【正确回复示例】
- "根据系统记录，您目前没有借阅中的图书。"
- "系统中暂无相关图书信息。"
- "知识库中没有找到关于此问题的答案。"

【错误回复示例】
- "虽然系统中没有，但我可以推荐《三体》..." ❌
- "您可能还喜欢这些书..." ❌
- "一般来说，图书馆会有..." ❌

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
        # 没有数据时使用较低temperature减少AI编造的可能性
        temp = 0.3 if db_data else 0.3
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
        支持多轮对话和对话状态管理
        """
        # 检查对话状态
        conv_state = conversation_manager.get_state(user_id)
        
        # 如果在确认阶段，检查用户是否确认或取消
        if conv_state and conversation_manager.is_confirming(user_id):
            # 检查确认词
            confirm_patterns = ['确认', '是的', '确定', '没问题', '就这样', '可以了', '同意', '好的', '好', '行', 'ok']
            cancel_patterns = ['取消', '不要', '算了', '否', '不借', '不预约', '不发布']
            
            is_confirm = any(word in user_message for word in confirm_patterns)
            is_cancel = any(word in user_message for word in cancel_patterns)
            
            if is_confirm:
                # 用户确认，执行操作
                pending = conv_state.get('pending_action', {})
                action = pending.get('action')
                params = pending.get('params', {})
                
                if action:
                    result = self._execute_action(action, params, user_id, user_role)
                    if result.get('success'):
                        yield f"✅ {result.get('message', '操作成功')}"
                        if result.get('data', {}).get('due_date'):
                            yield f"\n\n应还日期：{result['data']['due_date']}"
                        if result.get('data', {}).get('reservation_id'):
                            yield f"\n\n预约号：{result['data']['reservation_id']}"
                    else:
                        yield f"❌ {result.get('message', '操作失败')}"
                    
                    conversation_manager.clear_state(user_id)
                    return
            
            elif is_cancel:
                # 用户取消
                yield "已取消操作。"
                conversation_manager.clear_state(user_id)
                return
        
        # 如果正在收集参数，提取新参数并更新状态
        if conv_state and conversation_manager.is_collecting(user_id):
            intent = conv_state['current_intent']
            
            # 【关键修复】意图切换检测：检查是否与当前intent完全不相关
            new_intent = self._analyze_intent(user_message)
            new_action = new_intent.get('action')
            new_category = new_intent.get('category', '')
            
            # 检查是否是明确的切换意图
            intent_switch = False
            if intent == 'create_reservation' and new_action in ['borrow_book', 'complete_task', 'publish_notification']:
                intent_switch = True
            elif intent == 'borrow_book' and new_action in ['create_reservation', 'complete_task', 'publish_notification']:
                intent_switch = True
            elif new_category == 'book' and intent != 'borrow_book' and new_action is None:
                # 借书查询类意图
                intent_switch = True
            elif new_category == 'notification' and intent not in ['publish_notification']:
                intent_switch = True
            elif new_category == 'task' and intent != 'create_task':
                intent_switch = True
            
            # 检查是否是明确的退出词
            cancel_patterns = [
                r'^取消|^算了|^不约了|^不借了|^不预约了|^不发布了|^算了|^不搞了',
            ]
            is_cancel = any(re.search(p, user_message, re.IGNORECASE) for p in cancel_patterns)
            
            if intent_switch or is_cancel:
                print(f"[INTENT_SWITCH] 检测到意图切换: 当前={intent}, 新意图={new_action or new_category}, 清除状态")
                conversation_manager.clear_state(user_id)
                # 不return，继续执行正常的意图识别流程
            else:
                params = self._extract_params(user_message, intent)
                
                # 【关键修复】如果正则提取不到参数，尝试智能提取
                if not params:
                    next_missing = conversation_manager.get_next_missing_param(user_id)
                    if next_missing:
                        param_name = next_missing[0]
                        smart_params = self._smart_extract_param(user_message, param_name, intent)
                        if smart_params:
                            params = smart_params
                            print(f"[SMART_EXTRACT] 智能提取到参数: {smart_params}")
                
                # 【关键修复】补充 venue_id：如果有 venue_name 但没有 venue_id，尝试搜索获取
                if intent == 'create_reservation' and params.get('venue_name') and not params.get('venue_id'):
                    venues = self._search_venue_by_name(params['venue_name'])
                    if len(venues) == 1:
                        params['venue_id'] = venues[0]['id']
                        print(f"[VENUE_FIX] 根据名称 '{params['venue_name']}' 找到 venue_id: {venues[0]['id']}")
                
                # 【关键修复】补充 end_time：如果只有 start_time 没有 end_time，默认+2小时
                if intent == 'create_reservation' and params.get('start_time') and not params.get('end_time'):
                    start_dt = datetime.strptime(params['start_time'], "%H:%M")
                    end_dt = start_dt + timedelta(hours=2)
                    params['end_time'] = end_dt.strftime("%H:%M")
                    print(f"[TIME_FIX] 自动补充 end_time: {params['end_time']} (start_time: {params['start_time']})")
                
                # 更新参数
                is_complete = conversation_manager.update_params(user_id, params)
            
            if is_complete:
                # 参数收集完成，进入确认阶段
                collected = conv_state['collected_params']
                
                # 查询相关信息用于确认展示
                if intent == 'create_reservation':
                    # 查询场地信息
                    venue_name = collected.get('venue_name', '')
                    if venue_name:
                        venues = self._search_venue_by_name(venue_name)
                        if len(venues) == 1:
                            collected['venue_id'] = venues[0]['id']
                            db_data = f"【数据库信息】\n场地信息：\n{json.dumps(venues[0], ensure_ascii=False, indent=2)}"
                        elif len(venues) > 1:
                            # 多个匹配，让用户选择
                            db_data = f"【数据库信息】\n找到多个匹配场地：\n{json.dumps(venues[:3], ensure_ascii=False, indent=2)}"
                            yield f"找到多个匹配场地，请选择：\n" + "\n".join([f"- {v['name']} (ID:{v['id']})" for v in venues[:3]])
                
                elif intent == 'borrow_book':
                    # 查询图书信息
                    book_title = collected.get('book_title', '')
                    if book_title:
                        books = self._search_book_by_title(book_title)
                        if books and len(books) > 0:
                            available = [b for b in books if b.get('available', 0) > 0]
                            if available:
                                collected['book_id'] = available[0]['id']
                                db_data = f"【数据库信息】\n图书查询结果：\n{json.dumps(available[0], ensure_ascii=False, indent=2)}"
                
                # 设置待执行操作
                conversation_manager.set_pending_action(user_id, intent, collected)
                
                # 发送 pending_action 给前端，用于显示确认UI
                pending_action_data = {
                    'action': intent,
                    'params': collected
                }
                yield f"__PENDING_ACTION__:{json.dumps(pending_action_data, ensure_ascii=False)}"
                
                # 【关键修复】生成确认摘要文本并返回，不再走AI流式生成
                if intent == 'create_reservation':
                    venue = collected.get('venue_name', collected.get('venue_id', '场地'))
                    date = collected.get('date', '')
                    start_time = collected.get('start_time', '')
                    end_time = collected.get('end_time', '')
                    purpose = collected.get('purpose', '')
                    yield f"好的！为您确认预约信息：\n- 场地：{venue}\n- 日期：{date}\n- 时间：{start_time}-{end_time}\n- 用途：{purpose}\n\n请回复【确认】完成预约。"
                elif intent == 'borrow_book':
                    book_title = collected.get('book_title', '')
                    yield f"好的！确认借阅《{book_title}》。请回复【确认】完成借阅。"
                
                return  # 关键：停止，不再走AI流式生成
            else:
                # 【关键修复】检查用户是否在询问相关查询（如场地列表、图书列表等）
                if not params:
                    # 检查是否是场地查询
                    venue_query_patterns = [
                        r'有什么场地|有哪些场地|有什么教室|有哪些教室|有什么会议室|有哪些会议室|有什么实验室|有哪些实验室',
                        r'场地列表|教室列表|会议室列表|实验室列表|可选场地|可用场地',
                        r'可以预约哪里|可以预约什么场地|能预约哪里|能用什么场地'
                    ]
                    is_venue_query = any(re.search(p, user_message, re.IGNORECASE) for p in venue_query_patterns)
                    
                    if is_venue_query and intent == 'create_reservation':
                        # 查询可用场地
                        venues = self._search_venue_by_name('')
                        if venues:
                            venue_list = "\n".join([f"- {v['name']} ({v.get('type', '场地')})" for v in venues[:10]])
                            yield f"可用的场地有：\n{venue_list}\n\n请告诉我您想预约哪个场地？"
                        else:
                            yield "抱歉，暂时没有可用的场地信息。\n\n请告诉我您想预约哪个场地？"
                        return
                    
                    # 检查是否是图书查询（在借书流程中）
                    book_query_patterns = [
                        r'有什么书|有哪些书|可以借什么|有什么图书|有哪些图书|推荐.*书',
                        r'书列表|图书列表|可借图书| available books'
                    ]
                    is_book_query = any(re.search(p, user_message, re.IGNORECASE) for p in book_query_patterns)
                    
                    if is_book_query and intent == 'borrow_book':
                        # 查询可借图书
                        books = self._search_book_by_title('')
                        available_books = [b for b in books if b.get('available', 0) > 0]
                        if available_books:
                            book_list = "\n".join([f"- 《{b['title']}》{b.get('author', '')} (可借{b['available']}本)" for b in available_books[:10]])
                            yield f"可借阅的图书有：\n{book_list}\n\n请告诉我您想借阅哪本书？"
                        else:
                            yield "抱歉，暂时没有可借的图书。\n\n请告诉我您想借阅哪本书？"
                        return
                
                # 【关键修复】如果提取不到参数，检查是否是无关消息
                if not params:
                    # 检查用户消息是否是明显的查询或无关内容
                    query_patterns = [
                        r'^你好|^您好|^嗨|^在吗|^在不在',
                        r'我借了什么书|我的借阅|借了什么|借了哪些|在借',
                        r'可以借什么|有哪些书|有什么书|推荐.*书',
                        r'我的预约|预约记录|有什么预约',
                        r'我的通知|未读通知|有什么通知',
                        r'我的任务|待办|有什么任务',
                        r'^查询|^查看|^显示|^列出',
                    ]
                    is_unrelated = any(re.search(pattern, user_message, re.IGNORECASE) for pattern in query_patterns)
                    
                    if is_unrelated:
                        print(f"[ESCAPE] 检测到无关消息，清除状态: {user_message}")
                        conversation_manager.clear_state(user_id)
                        # 不return，继续执行正常意图识别
                    else:
                        # 正常参数收集流程
                        prompt = conversation_manager.get_missing_params_prompt(user_id, ask_one_by_one=True)
                        yield prompt
                        return
                else:
                    # 有参数但被update_params过滤了，继续正常询问
                    prompt = conversation_manager.get_missing_params_prompt(user_id, ask_one_by_one=True)
                    yield prompt
                    return
        
        # 正常意图识别
        intent = self._analyze_intent(user_message)
        context_parts = []
        
        # 处理新意图的初始化
        if intent.get('action') in ['create_reservation', 'borrow_book', 'publish_notification', 'create_task']:
            params = intent.get('params', {})
            
            # 【关键修复】用 _extract_params 从原始消息中提取完整参数（修正AI返回的键名）
            extracted = self._extract_params(user_message, intent['action'])
            if extracted:
                # 用 extracted 补充/覆盖 params（extracted 的键名更准确）
                for key, value in extracted.items():
                    if value:
                        params[key] = value  # 直接覆盖，确保键名正确
                
                # 【关键修复】处理AI意图识别的非标准键名映射
                if params.get('resource') and not params.get('venue_name'):
                    # AI返回 resource 而非 venue_name，需要映射
                    venue_name = params['resource']
                    # 移除错误的键
                    if 'resource' in params:
                        del params['resource']
                    # 提取场地名称
                    venue_match = re.search(r'(会议室|实验室|自习室|教室)', venue_name)
                    if venue_match:
                        # 查找具体场地（如"会议室-1"）
                        venue_id_match = re.search(r'(\d+)', venue_name)
                        if venue_id_match:
                            venue_name = f"{venue_match.group(1)}-{venue_id_match.group(1)}"
                        else:
                            venue_name = venue_match.group(1)
                    params['venue_name'] = venue_name
                
                if params.get('time') and not params.get('date'):
                    # AI返回 time 而非 date，需要解析
                    time_str = params['time']
                    if '明天' in time_str or '今日' in time_str:
                        params['date'] = parse_date(time_str)
                    # 移除错误的键
                    if 'time' in params and not params.get('start_time'):
                        del params['time']
                
                print(f"[EXTRACT_FIX] 补充参数: {extracted}, 最终: {params}")
            
            # 关键修复：如果有场地名称但没有venue_id，尝试搜索获取
            if intent['action'] == 'create_reservation' and params.get('venue_name') and not params.get('venue_id'):
                venues = self._search_venue_by_name(params['venue_name'])
                if len(venues) == 1:
                    params['venue_id'] = venues[0]['id']
                    print(f"[DEBUG] 根据名称 '{params['venue_name']}' 找到场地ID: {venues[0]['id']}")
                elif len(venues) > 1:
                    # 多个匹配，列出选项
                    venue_list = "\n".join([f"- {v['name']} (ID:{v['id']})" for v in venues[:5]])
                    yield f"找到多个匹配场地，请选择：\n{venue_list}"
                    return
            
            # 关键修复：如果有书名但没有book_id，尝试搜索获取  
            if intent['action'] == 'borrow_book' and params.get('book_title') and not params.get('book_id'):
                books = self._search_book_by_title(params['book_title'])
                if books and len(books) > 0:
                    available = [b for b in books if b.get('available', 0) > 0]
                    if available:
                        params['book_id'] = available[0]['id']
                        print(f"[DEBUG] 根据书名 '{params['book_title']}' 找到图书ID: {available[0]['id']}")
            
            # 兼容意图识别返回的参数名
            if params.get('venue') and not params.get('venue_name'):
                params['venue_name'] = params['venue']
            
            missing_params = self._get_missing_params(intent['action'], params)
            
            if missing_params:
                # 需要收集更多参数
                conversation_manager.init_conversation(
                    user_id=user_id,
                    intent=intent['action'],
                    collected_params=params,
                    missing_params=missing_params
                )
                # 逐个询问缺失参数（使用详细版）
                prompt = conversation_manager.get_missing_params_prompt(user_id, ask_one_by_one=True)
                yield prompt
                return
        
        # 获取知识库内容
        kb_context = knowledge_base.get_relevant_context(user_message)
        if kb_context:
            context_parts.append(f"【知识库信息】\n{kb_context}")
        
        if db_data:
            context_parts.append(f"【数据库信息】\n{db_data}")
        
        system_prompt = f"""你是智慧校园AI助手，当前为已登录的{user_role}用户提供服务。

当前时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}

【数据来源约束 - 最高优先级，必须严格遵守】
1. 你只拥有以下两类信息来源：
   - 【数据库信息】：系统从数据库实时查询的用户个人数据
   - 【知识库信息】：系统从知识库文档中检索的校园相关信息

2. 严禁使用训练数据：禁止使用你预训练知识中的任何信息回答用户问题

3. 数据为空时的处理：
   - 如果【数据库信息】为空 → 回复"系统中暂无您的相关记录"
   - 如果【知识库信息】为空 → 回复"系统中暂无相关信息"
   - 如果两者都为空 → 回复"系统中暂无相关信息，无法回答您的问题"

【绝对禁止的行为】
- 严禁编造任何数据、记录、图书、人物、事件
- 严禁推荐数据库中不存在的图书
- 严禁假设、推测、生成看似合理但实际不存在的信息
- 严禁使用"比如"、"例如"来列举系统未提供的内容
- 严禁说"我可以为您推荐..."然后编造推荐内容

【正确回复示例】
- "根据系统记录，您目前没有借阅中的图书。"
- "系统中暂无相关图书信息。"
- "知识库中没有找到关于此问题的答案。"

【错误回复示例】
- "虽然系统中没有，但我可以推荐《三体》..." ❌
- "您可能还喜欢这些书..." ❌
- "一般来说，图书馆会有..." ❌

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

【角色定位 - 最重要】
你只是查询助手，只负责查询和展示信息，绝不执行任何操作！
所有办理、执行、提交等操作都必须由用户回复【确认】完成，不是你来做。

【绝对禁止 - 违反会导致系统错误】
- 绝对禁止说"✅办理成功"、"✅借阅成功"、"✅预约成功"、"✅发布成功"
- 绝对禁止说"办理完成"、"已完成"、"已提交"、"已办理"
- 绝对禁止说"正在办理"、"办理中"、"已为您办理"等暗示你在执行的话
- 绝对禁止编造任何办理结果！

【办理业务流程 - 必须遵守】
1. 当用户说"帮我借书/预约/发布..."时，系统会逐个询问所需参数（日期、时间等）
2. 你的角色是确认理解用户需求，并友好地询问下一个参数
3. 每次只询问一个参数，收到回答后确认并继续询问下一个
4. 所有参数收集完成后，展示完整信息供用户确认
5. 【必须】提示用户"请回复【确认】完成办理"或"是否确认？"
6. 【严禁】在用户点击确认前说任何"成功"、"完成"的话

【参数收集对话示例 - 必须遵循】
用户："预约a02自习室"
AI："好的！您想预约a02自习室。请告诉我日期是哪一天？"

用户："明天"
AI："好的，预约a02自习室，日期是明天。请告诉我时间段是几点到几点？"

用户："下午2点到4点"
AI："好的，预约a02自习室，日期是明天，时间段是下午2点到4点。请告诉我用途是什么？"

用户："学习"
AI："好的！为您确认预约信息：
- 场地：a02自习室
- 日期：明天（2026-04-26）
- 时间：14:00-16:00
- 用途：学习
是否确认预约？"

【正确回复模板】
- 收集参数中："好的！您想[操作]。请告诉我[参数]是[询问语]？"
- 确认收到参数："好的，[已收集的信息]。请告诉我[下一个参数]是[询问语]？"
- 参数收集完成：展示完整信息，提示"请回复【确认】完成[操作]"
- 【严禁AI说】"✅办理成功"、"✅借阅成功"、"✅预约成功" - 这些话只能由系统在用户点击确认后显示

你的职责：
1. 解答校园相关问题
2. 基于提供的数据回答用户问题（禁止编造）
3. 记住之前的对话内容，保持上下文连贯
4. 保持友好、专业、耐心的态度
5. 【绝不执行操作】只查询和询问确认
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
        # 没有数据时使用较低temperature减少AI编造的可能性
        temp = 0.3 if db_data else 0.3
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
                parsed_date = parse_date(date_match.group(1))
                if parsed_date:
                    params["date"] = parsed_date
            
            # 提取时间范围
            start_time, end_time = extract_time_range(message)
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            
            # 【关键修复】如果 extract_time_range 失败，尝试用 parse_time 提取单个时间点
            if not start_time:
                # 尝试解析 "上午10点" 或 "10点" 格式
                time_match = re.search(r'(上午|下午|早上|晚上)?([零一二三四五六七八九十\d]{1,3})点', message)
                if time_match:
                    period, hour_str = time_match.groups()
                    single_time = parse_time(f"{period or ''}{hour_str}点")
                    if single_time:
                        params["start_time"] = single_time
                        # 默认结束时间 = 开始时间 + 2小时
                        start_dt = datetime.strptime(single_time, "%H:%M")
                        end_dt = start_dt + timedelta(hours=2)
                        params["end_time"] = end_dt.strftime("%H:%M")
                        print(f"[TIME_EXTRACT] 从消息中提取单个时间点: {single_time}-{params['end_time']}")
            
            # 如果用户说类似"明天上午十点"但没有结束时间，默认2小时
            if start_time and not end_time:
                start_dt = datetime.strptime(start_time, "%H:%M")
                end_dt = start_dt + timedelta(hours=2)
                params["end_time"] = end_dt.strftime("%H:%M")
            
            # 兼容旧版 time 参数
            if params.get('start_time') and not params.get('time'):
                params['time'] = params['start_time']
            
            # 提取场地名称 - 支持多种格式
            # 格式1: 类型+数字（如会议室1、实验室2、自习室3）
            venue_match = re.search(r'(会议室|实验室|自习室|教室)(\d{1,4})', message)
            if venue_match:
                venue_name = venue_match.group(1) + venue_match.group(2)
                params["venue_name"] = venue_name
                venues = self._search_venue_by_name(venue_name)
                if len(venues) == 1:
                    params["venue_id"] = venues[0]['id']
            else:
                # 格式2: 字母+数字（如a02, B205, a1, B2）
                venue_match = re.search(r'([a-zA-Z]\d{1,4})\s*(?:自习室|教室|实验室|会议室)?', message, re.IGNORECASE)
                if venue_match:
                    venue_name = venue_match.group(1).upper()
                    params["venue_name"] = venue_name
                    venues = self._search_venue_by_name(venue_name)
                    if len(venues) == 1:
                        params["venue_id"] = venues[0]['id']
                else:
                    # 格式3: 纯数字房间号（如302, 205）
                    venue_match = re.search(r'(\d{3,4})\s*(?:自习室|教室|实验室|会议室)?', message)
                    if venue_match:
                        venue_name = venue_match.group(1)
                        params["venue_name"] = venue_name
                        venues = self._search_venue_by_name(venue_name)
                        if len(venues) == 1:
                            params["venue_id"] = venues[0]['id']
            
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
            
            # 提取用途
            purpose_keywords = {
                "学习": "学习",
                "自习": "学习",
                "会议": "会议",
                "开会": "会议",
                "实验": "实验",
                "讨论": "小组讨论"
            }
            for keyword, purpose in purpose_keywords.items():
                if keyword in message:
                    params["purpose"] = purpose
                    break
            
            # 注意：不再设置默认用途，让AI询问用户
        
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
    
    def _smart_extract_param(self, message: str, param_name: str, intent: str = None) -> Dict:
        """
        根据缺失的参数类型，智能提取参数
        用于在正则提取失败时，根据上下文智能提取
        """
        import re
        params = {}
        
        if param_name in ['start_time', 'end_time']:
            # 全力提取时间
            # 尝试提取时间范围
            start_time, end_time = extract_time_range(message)
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
            
            # 如果只提取到一个时间，作为开始时间
            if not start_time and not end_time:
                # 尝试提取单个时间
                time_match = re.search(r'(上午|下午|早上|晚上)?([零一二三四五六七八九十\d]{1,3})点', message)
                if time_match:
                    period, hour_str = time_match.groups()
                    hour = chinese_to_arabic(hour_str) if any(c in hour_str for c in '零一二三四五六七八九十') else int(hour_str)
                    if period in ['下午', '晚上'] and hour != 12:
                        hour += 12
                    time_val = f"{hour:02d}:00"
                    if param_name == 'start_time':
                        params['start_time'] = time_val
                        # 自动补充 end_time
                        start_dt = datetime.strptime(time_val, "%H:%M")
                        end_dt = start_dt + timedelta(hours=2)
                        params['end_time'] = end_dt.strftime("%H:%M")
                    elif param_name == 'end_time':
                        params['end_time'] = time_val
        
        elif param_name == 'date':
            # 提取日期
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}月\d{1,2}日|明天|后天|今天|大后天)', message)
            if date_match:
                parsed_date = parse_date(date_match.group(1))
                if parsed_date:
                    params['date'] = parsed_date
        
        elif param_name == 'purpose':
            # 直接作为用途（只要不是疑问句）
            if not any(q in message for q in ['?', '？', '吗', '呢', '什么', '哪', '多少']):
                # 过滤掉常见的非用途词
                non_purpose = ['你好', '好的', '谢谢', '再见', '嗯', '哦', '啊']
                if message.strip() not in non_purpose:
                    params['purpose'] = message.strip()
        
        elif param_name in ['venue', 'venue_id'] and intent == 'create_reservation':
            # 尝试提取场地名称
            # 格式1: 类型+数字
            venue_match = re.search(r'(会议室|实验室|自习室|教室)([零一二三四五六七八九十\d]{1,4})', message)
            if venue_match:
                type_name = venue_match.group(1)
                num_str = venue_match.group(2)
                if any(c in num_str for c in '零一二三四五六七八九十'):
                    num = chinese_to_arabic(num_str)
                else:
                    num = int(num_str)
                venue_name = f"{type_name}{num}"
                params['venue_name'] = venue_name
                venues = self._search_venue_by_name(venue_name)
                if len(venues) == 1:
                    params['venue_id'] = venues[0]['id']
            else:
                # 格式2: 字母+数字
                venue_match = re.search(r'([a-zA-Z][零一二三四五六七八九十\d]{1,4})', message, re.IGNORECASE)
                if venue_match:
                    venue_name = venue_match.group(1).upper()
                    params['venue_name'] = venue_name
                    venues = self._search_venue_by_name(venue_name)
                    if len(venues) == 1:
                        params['venue_id'] = venues[0]['id']
                else:
                    # 格式3: 纯数字
                    venue_match = re.search(r'([零一二三四五六七八九十\d]{3,4})', message)
                    if venue_match:
                        num_str = venue_match.group(1)
                        if any(c in num_str for c in '零一二三四五六七八九十'):
                            num = chinese_to_arabic(num_str)
                        else:
                            num = int(num_str)
                        venue_name = str(num)
                        params['venue_name'] = venue_name
                        venues = self._search_venue_by_name(venue_name)
                        if len(venues) == 1:
                            params['venue_id'] = venues[0]['id']
        
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
                # 标记用户指定的书名，帮助AI识别
                return f"【数据库信息】\n用户想借的书名：{keyword}\n查询结果（共{len(books)}本）：\n{json.dumps(books, ensure_ascii=False, indent=2)}"
        
        elif category == "reservation":
            reservations = db_tools.query_user_reservations(user_id)
            if any("error" in r for r in reservations):
                return f"查询出错：{reservations[0].get('error', '未知错误')}"
            return f"您的预约记录（共{len(reservations)}条）：\n{json.dumps(reservations, ensure_ascii=False, indent=2)}"
        
        elif category == "venue":
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
            
            # 获取所有必要参数
            venue_id = params.get("venue_id")
            date = params.get("date")
            start_time = params.get("start_time")
            end_time = params.get("end_time")
            purpose = params.get("purpose", "学习")
            
            # 检查必需参数
            if not all([venue_id, date, start_time, end_time]):
                missing = []
                if not venue_id: missing.append("场地")
                if not date: missing.append("日期")
                if not start_time: missing.append("开始时间")
                if not end_time: missing.append("结束时间")
                result["message"] = f"请提供以下信息：{', '.join(missing)}"
                result["needs_more_info"] = True
                return result
            
            # 执行预约
            db_result = db_tools.create_reservation(
                user_id=user_id,
                venue_id=venue_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                purpose=purpose
            )
            result.update(db_result)
        
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
    
    def _get_missing_params(self, intent: str, params: Dict) -> List[str]:
        """
        获取缺失的必要参数
        """
        required_params = {
            'create_reservation': ['date', 'start_time', 'end_time', 'purpose'],
            'borrow_book': ['book_title'],
            'publish_notification': ['title', 'content'],
            'create_task': ['title', 'content', 'task_type', 'end_date', 'target_type']
        }
        
        required = required_params.get(intent, [])
        missing = []
        
        for param in required:
            if not params.get(param):
                missing.append(param)
        
        # 特殊处理：场地预约需要 venue_id 或 venue_name 任一
        if intent == 'create_reservation':
            if not params.get('venue_id') and not params.get('venue_name'):
                missing.append('venue')
        
        # 特殊处理：借书需要 book_id 或 book_title 任一
        if intent == 'borrow_book':
            if not params.get('book_id') and not params.get('book_title'):
                missing.append('book_title')
        
        return missing
    
    def _search_venue_by_name(self, venue_name: str) -> List[Dict]:
        """
        根据场地名称搜索场地
        支持模糊匹配和同义词匹配
        """
        from services.db_tools import db_tools
        
        # 查询所有可用场地
        venues = db_tools.query_venues()
        
        if not venues or any("error" in v for v in venues):
            return []
        
        # 同义词映射（用户可能说的名称 -> 数据库中的关键词）
        synonyms = {
            '会议室': ['会议室', '讨论室', '会议'],
            '讨论室': ['会议室', '讨论室', '会议'],
            '自习室': ['自习室', '图书馆'],
            '教室': ['教室', '多媒体'],
            '实验室': ['实验室', '计算机']
        }
        
        matched = []
        search_lower = venue_name.lower()
        
        # 提取数字部分
        import re
        number_match = re.search(r'\d+', venue_name)
        search_number = number_match.group() if number_match else ''
        
        for venue in venues:
            venue_name_lower = venue.get('name', '').lower()
            room_no_lower = str(venue.get('room_no', '')).lower()
            
            # 1. 直接包含匹配
            if search_lower in venue_name_lower or search_lower in room_no_lower:
                matched.append(venue)
                continue
            
            # 2. 同义词匹配（如用户说"会议室1"，匹配"讨论室-1"）
            for keyword, related_words in synonyms.items():
                if keyword in search_lower:
                    # 检查场地名称是否包含相关词
                    for related in related_words:
                        if related in venue_name_lower:
                            # 同时检查数字是否匹配
                            if search_number and search_number in venue_name_lower:
                                matched.append(venue)
                                break
                            # 或者检查房间号
                            elif search_number and search_number in room_no_lower:
                                matched.append(venue)
                                break
                    break
            
            # 3. 数字匹配（如果输入主要是数字）
            if search_number and not matched:
                if search_number == room_no_lower:
                    matched.append(venue)
        
        # 去重
        seen_ids = set()
        unique_matched = []
        for venue in matched:
            if venue['id'] not in seen_ids:
                seen_ids.add(venue['id'])
                unique_matched.append(venue)
        
        return unique_matched
    
    def _search_book_by_title(self, book_title: str) -> List[Dict]:
        """
        根据书名搜索图书
        """
        from services.db_tools import db_tools
        return db_tools.query_books(keyword=book_title, limit=5)
    
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
