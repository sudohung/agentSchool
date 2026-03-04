# 消息发送模块返回值优化

## 📝 修改概述

本次优化将飞书消息发送模块的所有函数的返回值从 `Promise<void>` 改为 `Promise<Object>`，统一返回飞书 API 的标准响应数据格式。

## 🎯 修改内容

### 1. 核心函数修改

#### `sendInteractiveCard` (内部函数)
- **修改前**: 无返回值
- **修改后**: 返回标准飞书 API 响应格式
```javascript
return {
    code: res.code || 0,
    msg: res.msg || 'success',
    data: {
        message_id: res.data?.message_id || ''
    }
};
```

#### `sendTextMessage`
- **修改前**: `Promise<void>`
- **修改后**: `Promise<Object>` - 返回飞书 API 响应结果

#### `sendCardMessage`
- **修改前**: `Promise<void>`
- **修改后**: `Promise<Object>` - 返回飞书 API 响应结果

#### `sendThinkingMessage`
- **修改前**: `Promise<void>`
- **修改后**: `Promise<Object>` - 返回飞书 API 响应结果

#### `sendErrorMessage`
- **修改前**: `Promise<void>`
- **修改后**: `Promise<Object>` - 返回飞书 API 响应结果

#### `sendAIResponse`
- **修改前**: `Promise<void>`
- **修改后**: `Promise<Object>` - 返回飞书 API 响应结果

#### `sendEventNotification`
- **修改前**: `Promise<void>`
- **修改后**: `Promise<Object>` - 返回飞书 API 响应结果

#### `sendEmptyResponse`
- **修改前**: `Promise<void>`
- **修改后**: `Promise<Object>` - 返回飞书 API 响应结果

#### `updateMessage` (新增功能)
- **功能**: 支持更新已发送的消息
- **返回值**: `Promise<Object>` - 返回飞书 API 响应结果
- **参数**: 
  - `client`: 飞书客户端实例
  - `messageId`: 要编辑的消息 ID
  - `msgType`: 消息类型（'text' 或 'interactive'）
  - `content`: 消息内容

### 2. 统一的响应格式

所有函数均返回以下标准格式：

```javascript
{
  code: 0,          // 状态码，0 表示成功
  msg: 'success',   // 响应消息
  data: {
    message_id: 'om_1234567890abcdef'  // 消息 ID
  }
}
```

## 💡 使用示例

### 1. 获取消息 ID

```javascript
const result = await sendTextMessage(client, chatId, 'Hello');
const messageId = result.data.message_id;
console.log('消息 ID:', messageId);
```

### 2. 检查发送状态

```javascript
const result = await sendCardMessage(client, chatId, '内容');
if (result.code === 0) {
    console.log('发送成功');
} else {
    console.error('发送失败:', result.msg);
}
```

### 3. 更新已发送的消息

```javascript
// 先发送一条消息
const result = await sendTextMessage(client, chatId, '原始内容');
const messageId = result.data.message_id;

// 然后更新它
await updateMessage(client, messageId, 'text', '更新后的内容');
```

### 4. AI 对话场景

```javascript
async function handleUserMessage(chatId, userMessage) {
    try {
        // 发送思考状态并获取消息 ID
        const thinkingResult = await sendThinkingMessage(client, chatId);
        console.log('思考消息 ID:', thinkingResult.data.message_id);
        
        // 调用 AI 服务
        const aiResponse = await callAI(userMessage);
        
        // 发送 AI 回复并获取消息 ID
        const responseResult = await sendAIResponse(client, chatId, userMessage, aiResponse);
        console.log('回复消息 ID:', responseResult.data.message_id);
        
    } catch (error) {
        // 发送错误消息
        const errorResult = await sendErrorMessage(client, chatId, error.message);
        console.log('错误消息 ID:', errorResult.data.message_id);
    }
}
```

## 📋 文件变更清单

### 修改的文件

1. **feishu-message-sender.js**
   - 修改所有消息发送函数的返回值
   - 添加 `updateMessage` 函数
   - 完善错误处理和日志记录

2. **index.js**
   - 导出新增的 `updateMessage` 函数

3. **README.md**
   - 更新所有函数的返回值说明
   - 添加响应数据格式说明章节
   - 更新使用示例
   - 添加快速开始部分的返回值演示

## ✅ 优势

1. **可追溯性**: 通过返回的消息 ID，可以追踪和管理已发送的消息
2. **错误处理**: 可以通过返回的 code 和 msg 判断发送状态
3. **后续操作**: 支持基于消息 ID 的更新、删除等后续操作
4. **统一标准**: 所有函数返回一致的格式，便于使用
5. **向后兼容**: 不影响现有的不关心返回值的用法

## ⚠️ 注意事项

1. 如果不需要使用返回值，可以忽略，不影响现有用法
2. 建议在需要消息管理时使用返回值获取消息 ID
3. 错误处理时建议检查返回的 code 字段

## 🔄 兼容性说明

- **向后兼容**: 现有代码无需修改，返回值是可选使用的
- **API 不变**: 函数参数和调用方式完全保持不变
- **平滑升级**: 可以直接替换旧版本，无需担心兼容性问题

---

**修改时间**: 2026-03-05  
**维护者**: 开发团队
