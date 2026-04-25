# -*- coding: utf-8 -*-
"""
RAG 知识库模块 - 简化版
支持 PDF、Word、Markdown 等格式的文档检索（基于关键词匹配）
"""
import os
import re
from typing import List, Dict, Optional
from pathlib import Path

# 文档解析库
try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document
    WORD_SUPPORT = True
except ImportError:
    WORD_SUPPORT = False


class SimpleKnowledgeBase:
    """简化版知识库管理类（不依赖向量数据库）"""
    
    def __init__(self, knowledge_dir: str = "./knowledge_base"):
        self.knowledge_dir = knowledge_dir
        self.documents = []  # 存储文档内容
        
        # 确保目录存在
        os.makedirs(knowledge_dir, exist_ok=True)
        
        # 启动时自动加载
        self.load_all_documents()
    
    def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        if not PDF_SUPPORT:
            return "[PDF解析不支持，请安装pypdf库]"
        
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"[PDF解析错误: {str(e)}]"
    
    def _parse_word(self, file_path: str) -> str:
        """解析Word文件"""
        if not WORD_SUPPORT:
            return "[Word解析不支持，请安装python-docx库]"
        
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            return f"[Word解析错误: {str(e)}]"
    
    def _parse_markdown(self, file_path: str) -> str:
        """解析Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 简单的Markdown格式清理
            content = re.sub(r'#+ ', '', content)  # 移除标题标记
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # 移除链接
            content = re.sub(r'\*\*?|\*\*?', '', content)  # 移除粗体斜体
            return content
        except Exception as e:
            return f"[Markdown解析错误: {str(e)}]"
    
    def load_document(self, file_path: str) -> Dict:
        """加载单个文档"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            content = self._parse_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            content = self._parse_word(file_path)
        elif ext in ['.md', '.markdown']:
            content = self._parse_markdown(file_path)
        elif ext in ['.txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            return {"success": False, "message": f"不支持的文件格式: {ext}"}
        
        file_name = os.path.basename(file_path)
        
        # 存储文档
        doc_entry = {
            "source": file_name,
            "content": content,
            "chunks": self._chunk_text(content)
        }
        
        # 检查是否已存在，存在则更新
        existing = [i for i, d in enumerate(self.documents) if d["source"] == file_name]
        if existing:
            self.documents[existing[0]] = doc_entry
        else:
            self.documents.append(doc_entry)
        
        return {
            "success": True,
            "message": f"成功加载 {file_name}",
            "chunks": len(doc_entry["chunks"]),
            "characters": len(content)
        }
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """将文本分块"""
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # 尽量在句子边界分割
            if end < len(text):
                for sep in ['。', '？', '！', '. ', '? ', '! ']:
                    pos = chunk.rfind(sep)
                    if pos > chunk_size * 0.5:
                        end = start + pos + 1
                        chunk = text[start:end]
                        break
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def load_all_documents(self) -> Dict:
        """加载知识库目录下所有文档"""
        results = []
        total_chunks = 0
        
        for file_name in os.listdir(self.knowledge_dir):
            file_path = os.path.join(self.knowledge_dir, file_name)
            if os.path.isfile(file_path):
                result = self.load_document(file_path)
                results.append(result)
                if result.get("success"):
                    total_chunks += result.get("chunks", 0)
        
        return {
            "success": True,
            "loaded": len([r for r in results if r.get("success")]),
            "total_chunks": total_chunks,
            "details": results
        }
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """基于关键词搜索知识库"""
        query_keywords = set(query.lower().split())
        results = []
        
        for doc in self.documents:
            # 对每个文档的每个块进行匹配
            for i, chunk in enumerate(doc["chunks"]):
                chunk_lower = chunk.lower()
                # 计算匹配的关键词数量
                match_count = sum(1 for kw in query_keywords if kw in chunk_lower)
                
                if match_count > 0:
                    results.append({
                        "content": chunk,
                        "source": doc["source"],
                        "chunk_index": i,
                        "score": match_count
                    })
        
        # 按匹配度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def get_relevant_context(self, query: str, max_length: int = 1500) -> str:
        """获取与查询相关的上下文"""
        results = self.search(query, top_k=3)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = f"【{result['source']}】\n{result['content']}\n"
            if current_length + len(content) > max_length:
                break
            context_parts.append(content)
            current_length += len(content)
        
        return "\n".join(context_parts)
    
    def list_documents(self) -> List[str]:
        """列出知识库中的所有文档"""
        return [doc["source"] for doc in self.documents]
    
    def clear(self):
        """清空知识库"""
        self.documents = []
        return True


# 全局知识库实例
knowledge_base = SimpleKnowledgeBase()
