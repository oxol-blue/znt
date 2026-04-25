import request from '@/utils/request'

export const chat = (data) => {
  return request.post('/ai/chat', data)
}

export const campusAssistant = (data) => {
  return request.post('/ai/assistant', data)
}

// 流式对话接口
export const campusAssistantStream = async (data, onMessage, onError, onComplete) => {
  const { question, context } = data
  const token = localStorage.getItem('token')

  try {
    const response = await fetch('/api/ai/assistant/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      },
      body: JSON.stringify({ question, context })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 使用 ReadableStream 直接处理
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        // 处理剩余 buffer
        if (buffer.trim()) {
          processSSELine(buffer.trim(), onMessage, onComplete)
        }
        onComplete && onComplete()
        break
      }

      // 解码并添加到 buffer
      buffer += decoder.decode(value, { stream: true })

      // 处理完整的 SSE 行
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留不完整的最后一行

      for (const line of lines) {
        processSSELine(line, onMessage, onComplete)
      }
    }
  } catch (err) {
    onError && onError(err)
  }
}

// 处理单行 SSE 数据
function processSSELine(line, onMessage, onComplete) {
  line = line.trim()
  if (!line) return

  // SSE 格式: data: {...}
  if (line.startsWith('data: ')) {
    const data = line.slice(6)
    
    if (data === '[DONE]') {
      onComplete && onComplete()
      return
    }

    try {
      const parsed = JSON.parse(data)
      onMessage && onMessage(parsed)
    } catch (e) {
      // 可能是数据被分割了，忽略
      console.debug('SSE parse skip:', data.substring(0, 50))
    }
  }
}

export const generateNotification = (data) => {
  return request.post('/ai/generate-notification', data)
}

export const aiHealthCheck = () => {
  return request.get('/ai/health')
}

// 知识库相关 API

export const searchKnowledgeBase = (data) => {
  return request.post('/ai/knowledge-base/search', data)
}

export const listKnowledgeDocuments = () => {
  return request.get('/ai/knowledge-base/documents')
}

export const reloadKnowledgeBase = () => {
  return request.post('/ai/knowledge-base/reload')
}

// 执行操作接口（如确认借书）
export const executeAction = (data) => {
  return request.post('/ai/execute-action', data)
}
