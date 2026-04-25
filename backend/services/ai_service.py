# -*- coding: utf-8 -*-
"""
DeepSeek AI 服务模块
集成 DeepSeek API 提供智能助手功能
"""
import requests
import json
from typing import List, Dict, Optional, Generator
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, DEEPSEEK_MODEL


class DeepSeekService:
    """DeepSeek AI 服务类"""
    
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
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "你好"}]
            temperature: 温度参数，控制创造性 (0-2)
            max_tokens: 最大生成token数
            stream: 是否流式返回
        
        Returns:
            API响应结果
        """
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
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        流式聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
        
        Yields:
            生成的文本片段
        """
        url = f"{self.api_base}/chat/completions"
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'stream': True
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=data,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]  # 去掉 "data: " 前缀
                        if line == '[DONE]':
                            break
                        try:
                            chunk = json.loads(line)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.RequestException as e:
            yield f'[错误: {str(e)}]'
    
    def simple_chat(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """
        简单聊天接口
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
        
        Returns:
            AI回复文本
        """
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
    
    def campus_assistant(self, user_message: str, user_role: str = 'student') -> str:
        """
        校园智能助手
        
        Args:
            user_message: 用户问题
            user_role: 用户角色 (student/teacher)
        
        Returns:
            AI回复
        """
        system_prompt = f"""你是一个专业的智慧校园助手，面向{user_role}用户提供服务。

你的职责：
1. 解答校园相关问题（图书馆、课程、活动、场地等）
2. 帮助用户使用系统功能
3. 提供学习和教学建议
4. 保持友好、专业、耐心的态度

约束条件：
- 仅回答校园相关内容
- 不提供违法违规信息
- 不泄露用户隐私
- 无法回答时引导用户联系管理员

当前时间：2026年"""

        return self.simple_chat(user_message, system_prompt)
    
    def analyze_borrow_data(self, borrow_records: List[Dict]) -> str:
        """分析借阅数据"""
        prompt = f"""请分析以下图书借阅数据，提供阅读建议：

借阅记录：
{json.dumps(borrow_records, ensure_ascii=False, indent=2)}

请从以下角度分析：
1. 阅读偏好分析
2. 阅读建议
3. 推荐相关书籍类型"""

        return self.simple_chat(prompt)
    
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
4. 语气正式但不失亲和力"""

        return self.simple_chat(prompt)


# 全局服务实例
deepseek_service = DeepSeekService()
