# -*- coding: utf-8 -*-
"""
对话状态管理模块
支持多轮对话和参数收集
状态以JSON格式存储在内存中（带过期清理）
"""
import json
import time
from typing import Dict, Optional, List, Any
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
    
    def get_missing_params_prompt(self, user_id: int) -> str:
        """
        获取缺失参数的提示语
        :param user_id: 用户ID
        :return: 提示语
        """
        state = self.get_state(user_id)
        if not state:
            return ""
        
        missing = state.get('missing_params', [])
        intent = state.get('current_intent', '')
        
        # 根据意图和缺失参数生成提示
        prompts = []
        param_names = {
            'date': '日期（如：明天、后天、2026-04-26）',
            'start_time': '开始时间（如：14:00、下午2点）',
            'end_time': '结束时间（如：16:00、下午4点）',
            'purpose': '用途（如：学习、会议、实验）',
            'venue_id': '场地',
            'book_title': '书名',
            'title': '标题',
            'content': '内容',
            'target_type': '目标人群（全体学生/教师/指定人）',
            'task_type': '任务类型（作业/考试/活动）',
            'end_date': '截止日期'
        }
        
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
