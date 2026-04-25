# -*- coding: utf-8 -*-
"""
对话状态管理模块
支持多轮对话和参数收集
状态以JSON格式存储在内存中（带过期清理）
"""
import json
import time
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timedelta


class ConversationState:
    """对话状态管理类"""
    
    def __init__(self, max_age_minutes: int = 30):
        """
        初始化
        :param max_age_minutes: 状态最大存活时间（分钟）
        """
        self._states: Dict[int, Dict] = {}  # user_id -> state
        self._max_age = max_age_minutes * 60  # 转换为秒
    
    def _clean_expired(self):
        """清理过期状态"""
        now = time.time()
        expired_users = [
            user_id for user_id, state in self._states.items()
            if now - state.get('last_update', 0) > self._max_age
        ]
        for user_id in expired_users:
            del self._states[user_id]
    
    def get_state(self, user_id: int) -> Optional[Dict]:
        """
        获取用户对话状态
        :param user_id: 用户ID
        :return: 状态字典或None
        """
        self._clean_expired()
        return self._states.get(user_id)
    
    def set_state(self, user_id: int, state: Dict):
        """
        设置用户对话状态
        :param user_id: 用户ID
        :param state: 状态字典
        """
        state['last_update'] = time.time()
        self._states[user_id] = state
    
    def clear_state(self, user_id: int):
        """
        清除用户对话状态
        :param user_id: 用户ID
        """
        if user_id in self._states:
            del self._states[user_id]
    
    def init_conversation(self, user_id: int, intent: str, 
                         collected_params: Dict = None,
                         missing_params: List[str] = None):
        """
        初始化对话
        :param user_id: 用户ID
        :param intent: 意图（如 create_reservation, borrow_book 等）
        :param collected_params: 已收集的参数
        :param missing_params: 缺失的参数列表
        """
        self.set_state(user_id, {
            'current_intent': intent,
            'collected_params': collected_params or {},
            'missing_params': missing_params or [],
            'pending_action': None,
            'step': 'collecting'  # collecting -> confirming -> executing -> completed
        })
    
    def update_params(self, user_id: int, new_params: Dict) -> bool:
        """
        更新已收集的参数
        :param user_id: 用户ID
        :param new_params: 新参数
        :return: 是否收集完成（所有参数都已收集）
        """
        state = self.get_state(user_id)
        if not state:
            return False
        
        # 合并新参数
        state['collected_params'].update(new_params)
        
        # 从缺失列表中移除已收集的参数
        for key in new_params.keys():
            if key in state['missing_params']:
                state['missing_params'].remove(key)
        
        # 特殊处理：venue_name 或 venue_id 满足 venue 的要求
        if 'venue' in state['missing_params']:
            if 'venue_name' in state['collected_params'] or 'venue_id' in state['collected_params']:
                state['missing_params'].remove('venue')
        
        # 检查是否收集完成
        is_complete = len(state['missing_params']) == 0
        
        if is_complete:
            state['step'] = 'confirming'
        
        self.set_state(user_id, state)
        return is_complete
    
    def set_pending_action(self, user_id: int, action: str, params: Dict):
        """
        设置待执行操作
        :param user_id: 用户ID
        :param action: 操作类型
        :param params: 操作参数
        """
        state = self.get_state(user_id)
        if state:
            state['pending_action'] = {
                'action': action,
                'params': params
            }
            state['step'] = 'confirming'
            self.set_state(user_id, state)
    
    def get_pending_action(self, user_id: int) -> Optional[Dict]:
        """
        获取待执行操作
        :param user_id: 用户ID
        :return: 待执行操作或None
        """
        state = self.get_state(user_id)
        if state:
            return state.get('pending_action')
        return None
    
    def confirm_action(self, user_id: int) -> Optional[Dict]:
        """
        确认执行操作
        :param user_id: 用户ID
        :return: 待执行的操作（用于执行）或None
        """
        state = self.get_state(user_id)
        if not state:
            return None
        
        pending = state.get('pending_action')
        if pending:
            state['step'] = 'executing'
            self.set_state(user_id, state)
            return pending
        return None
    
    def complete_action(self, user_id: int, success: bool, result: Any = None):
        """
        完成操作
        :param user_id: 用户ID
        :param success: 是否成功
        :param result: 操作结果
        """
        state = self.get_state(user_id)
        if state:
            state['step'] = 'completed'
            state['result'] = {
                'success': success,
                'data': result
            }
            self.set_state(user_id, state)
    
    def is_collecting(self, user_id: int) -> bool:
        """是否在收集参数阶段"""
        state = self.get_state(user_id)
        return state is not None and state.get('step') == 'collecting'
    
    def is_confirming(self, user_id: int) -> bool:
        """是否在确认阶段"""
        state = self.get_state(user_id)
        return state is not None and state.get('step') == 'confirming'
    
    def get_next_missing_param(self, user_id: int) -> Optional[Tuple[str, str, str]]:
        """
        获取下一个缺失的参数（参数名, 参数描述, 询问语）
        :return: (param_name, param_desc, question) 或 None
        """
        state = self.get_state(user_id)
        if not state:
            return None
        
        missing = state.get('missing_params', [])
        if not missing:
            return None
        
        param_names = {
            'date': ('日期', '是哪一天'),
            'start_time': ('开始时间', '从几点开始'),
            'end_time': ('结束时间', '到几点结束'),
            'purpose': ('用途', '用途是什么'),
            'venue': ('场地', '是什么'),
            'venue_id': ('场地', '是什么'),
            'book_title': ('书名', '书名是什么'),
            'title': ('标题', '标题是什么'),
            'content': ('内容', '内容是什么'),
            'target_type': ('目标人群', '面向哪些人群'),
            'task_type': ('任务类型', '任务类型是什么'),
            'end_date': ('截止日期', '截止日期是哪一天')
        }
        
        # 返回第一个缺失的参数
        next_param = missing[0]
        desc, question = param_names.get(next_param, (next_param, f'{next_param}是什么'))
        return (next_param, desc, question)
    
    def get_progress_summary(self, user_id: int) -> str:
        """
        生成已收集参数的摘要，用于确认理解
        :param user_id: 用户ID
        :return: 摘要字符串
        """
        state = self.get_state(user_id)
        if not state:
            return ""
        
        intent = state.get('current_intent', '')
        collected = state.get('collected_params', {})
        
        parts = []
        
        if intent == 'create_reservation':
            if collected.get('venue_name'):
                parts.append(f"预约{collected['venue_name']}")
            elif collected.get('venue_id'):
                parts.append("预约场地")
            if collected.get('date'):
                parts.append(f"日期是{collected['date']}")
            if collected.get('start_time') and collected.get('end_time'):
                parts.append(f"时间段是{collected['start_time']}-{collected['end_time']}")
            if collected.get('purpose'):
                parts.append(f"用途是{collected['purpose']}")
        
        elif intent == 'borrow_book':
            if collected.get('book_title'):
                parts.append(f"借阅《{collected['book_title']}》")
            elif collected.get('book_id'):
                parts.append("借阅图书")
        
        elif intent == 'publish_notification':
            if collected.get('title'):
                parts.append(f"发布通知'{collected['title']}'")
        
        if parts:
            return "，".join(parts)
        return ""
    
    def get_missing_params_prompt(self, user_id: int, ask_one_by_one: bool = True) -> str:
        """
        获取缺失参数的提示语（逐个询问模式）
        :param user_id: 用户ID
        :param ask_one_by_one: 是否逐个询问（True逐个，False一次性列出）
        :return: 提示语
        """
        state = self.get_state(user_id)
        if not state:
            return ""
        
        missing = state.get('missing_params', [])
        intent = state.get('current_intent', '')
        collected = state.get('collected_params', {})
        
        # 逐个询问模式
        if ask_one_by_one and missing:
            next_param = self.get_next_missing_param(user_id)
            if next_param:
                param_name, param_desc, question = next_param
                
                # 生成确认理解的回复
                if intent == 'create_reservation':
                    venue = collected.get('venue_name', collected.get('venue_id', '场地'))
                    progress = self.get_progress_summary(user_id)
                    if progress:
                        return f"好的！{progress}。请告诉我{param_desc}{question}？"
                    else:
                        return f"好的！您想预约{venue}。请告诉我{param_desc}{question}？"
                
                elif intent == 'borrow_book':
                    book = collected.get('book_title', '图书')
                    progress = self.get_progress_summary(user_id)
                    if progress and progress != f"借阅《{book}》":
                        return f"好的！{progress}。请告诉我{param_desc}{question}？"
                    else:
                        return f"好的！您想借阅《{book}》。请告诉我{param_desc}{question}？"
                
                elif intent == 'publish_notification':
                    return f"好的！您想发布通知。请告诉我{param_desc}{question}？"
                
                elif intent == 'create_task':
                    return f"好的！您想创建任务。请告诉我{param_desc}{question}？"
                
                else:
                    return f"好的！请告诉我{param_desc}{question}？"
        
        # 一次性列出所有缺失参数（兼容旧模式）
        param_names = {
            'date': '日期（如：明天、后天、2026-04-26）',
            'start_time': '开始时间（如：14:00、下午2点）',
            'end_time': '结束时间（如：16:00、下午4点）',
            'purpose': '用途（如：学习、会议、实验）',
            'venue_id': '场地',
            'venue': '场地',
            'book_title': '书名',
            'title': '标题',
            'content': '内容',
            'target_type': '目标人群（全体学生/教师/指定人）',
            'task_type': '任务类型（作业/考试/活动）',
            'end_date': '截止日期'
        }
        
        prompts = []
        for param in missing:
            name = param_names.get(param, param)
            prompts.append(f"• {name}")
        
        if intent == 'create_reservation':
            return f"请提供以下预约信息：\n" + "\n".join(prompts)
        elif intent == 'borrow_book':
            return f"请提供借阅信息：\n" + "\n".join(prompts)
        elif intent == 'publish_notification':
            return f"请提供通知信息：\n" + "\n".join(prompts)
        elif intent == 'create_task':
            return f"请提供任务信息：\n" + "\n".join(prompts)
        else:
            return f"请提供以下信息：\n" + "\n".join(prompts)
    
    def get_all_states(self) -> Dict:
        """获取所有状态（用于调试）"""
        self._clean_expired()
        return self._states


# 全局实例
conversation_manager = ConversationState()
