# 智慧校园AI助手 - 增强功能使用说明

## 功能概述

本次更新为AI助手添加了以下增强功能：

1. **📚 知识库RAG**：支持PDF、Word、Markdown格式的文档检索
2. **🔍 数据库查询**：AI可直接查询数据库回答用户问题
3. **📝 智能操作**：支持通过AI发布通知、办理预约等操作
4. **✨ 意图识别**：自动识别用户意图，提供精准服务

---

## 安装依赖

```bash
# 进入后端目录
cd backend

# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 或者使用 pip
pip install -r requirements.txt
```

### 额外依赖说明

增强功能需要以下额外依赖：
- `chromadb` - 向量数据库
- `sentence-transformers` - 文本嵌入模型
- `pypdf` - PDF解析
- `python-docx` - Word文档解析

---

## 知识库使用

### 1. 添加知识库文档

将需要AI学习的文档放入 `knowledge_base/` 目录：

```
knowledge_base/
├── campus_guide.md      # 校园指南
├── library_rules.pdf    # 图书馆规则
├── course_info.docx     # 课程信息
└── ...
```

**支持的格式**：
- `.md` - Markdown文档
- `.pdf` - PDF文档
- `.docx` - Word文档
- `.txt` - 纯文本

### 2. 重新加载知识库

教师/管理员可在AI助手页面点击【重新加载知识库】按钮，或调用API：

```bash
POST /api/ai/knowledge-base/reload
```

### 3. 搜索知识库

```bash
POST /api/ai/knowledge-base/search
Content-Type: application/json

{
  "query": "图书馆开放时间",
  "top_k": 5
}
```

---

## API接口

### 智能对话接口

```bash
POST /api/ai/chat
Content-Type: application/json

{
  "message": "我借了哪些书？"
}
```

**响应示例**：
```json
{
  "code": 200,
  "data": {
    "response": "您的借阅记录如下：\n1. 《Python编程》...",
    "context_used": true,
    "intent": {
      "category": "borrow",
      "needs_db_query": true
    }
  }
}
```

### AI辅助生成通知

```bash
POST /api/ai/generate-notification
Content-Type: application/json

{
  "title": "关于期中考试的通知",
  "type": "announcement",
  "target": "全体师生",
  "auto_publish": true  // 直接发布
}
```

---

## 使用示例

### 学生端查询示例

| 用户输入 | AI响应 |
|---------|--------|
| "我借了哪些书？" | 查询数据库返回借阅记录 |
| "帮我查一下《Python编程》这本书" | 搜索图书并返回可借数量 |
| "我的预约记录" | 查询用户的场地预约 |
| "有哪些未读通知？" | 查询未读通知列表 |
| "图书馆什么时候开放？" | 基于知识库回答 |

### 教师端操作示例

| 用户输入 | AI响应 |
|---------|--------|
| "发布关于五一放假的通知" | 生成并发布通知 |
| "帮我写一份学术讲座通知" | 生成通知内容供确认 |
| "查看我发布的任务" | 查询教师发布的任务 |

---

## 系统架构

```
用户输入
   │
   ▼
┌─────────────────────────────────────────┐
│           AI Agent (DeepSeek)            │
│  ┌──────────────┐  ┌──────────────┐    │
│  │   意图识别    │  │   任务路由    │    │
│  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────┘
          │                 │
    ┌─────┘                 └─────┐
    ▼                             ▼
┌──────────────┐           ┌──────────────┐
│   知识库 RAG  │           │   数据库工具  │
│  (ChromaDB)  │           │  (MySQL)     │
└──────────────┘           └──────────────┘
          │                             │
          └─────────────┬───────────────┘
                        ▼
              ┌──────────────────┐
              │    回复生成       │
              │  (DeepSeek API)  │
              └──────────────────┘
                        │
                        ▼
                    用户响应
```

---

## 注意事项

1. **首次使用知识库**：需要先将文档放入 `knowledge_base/` 目录并点击"重新加载"
2. **Embedding模型**：首次运行会自动下载 `BAAI/bge-large-zh-v1.5` 模型
3. **API限制**：DeepSeek API有调用频率限制，请合理使用
4. **数据安全**：知识库文档仅供内部使用，不要包含敏感信息

---

## 故障排查

### 知识库搜索无结果
- 检查文档是否放入 `knowledge_base/` 目录
- 确认已点击"重新加载知识库"
- 查看文档格式是否支持

### AI无法查询数据库
- 检查数据库连接配置
- 确认用户已登录（需要user_id）
- 查看后端日志

### Embedding模型下载慢
```bash
# 手动下载模型
git lfs install
git clone https://huggingface.co/BAAI/bge-large-zh-v1.5
```

---

## 更新日志

### v0.2.0 (2024-04-24)
- ✨ 新增知识库RAG功能
- ✨ 新增数据库查询能力
- ✨ 新增智能操作（发布通知）
- ✨ 新增意图识别
- 💄 优化AI助手界面

---

如有问题，请联系系统管理员。
