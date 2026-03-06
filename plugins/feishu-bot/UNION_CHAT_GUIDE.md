# 外部群/联合群创建指南

## 概述

外部群（联合群）是飞书提供的跨组织群聊功能，允许不同企业/组织的成员在同一个群聊中协作。

## 群聊类型

### chat_type 参数说明

| 值 | 说明 | 使用场景 |
|---|---|---|
| `private` | 私有群（默认） | 企业内部私有群聊 |
| `public` | 公共群 | 企业内部公开群聊 |
| `union` | **联合群/外部群** | 跨组织群聊 |
| `p2p_chat` | 单聊 | 一对一聊天 |

### user_id_type 参数说明

| 值 | 说明 | 适用场景 |
|---|---|---|
| `open_id` | 应用级用户 ID | 同一应用内的用户标识 |
| `union_id` | 平台级用户 ID | **跨应用、跨组织的用户标识** |
| `user_id` | 企业自定义用户 ID | 企业内部系统对接 |

## 创建外部群的前提条件

### 1. 权限配置

在飞书开放平台后台，为应用申请以下权限：

```
权限管理 → 即时通信
✓ im:chat              - 创建群聊
✓ im:union_chat        - 创建联合群聊（需要申请）
✓ contact:user:union_id - 获取用户 union_id
```

### 2. 企业合作关系

- 双方企业必须在飞书后台建立**商务合作关系**
- 合作关系建立后，才能互相邀请对方的成员加入联合群
- 企业管理员需要在飞书管理后台完成合作认证

### 3. 用户 ID 获取

外部用户必须使用 `union_id`，获取方式：

#### 方式 1: 用户授权回调

```javascript
// 用户授权后，回调中会包含 union_id
{
    "open_id": "ou_xxxxxx",
    "union_id": "on_xxxxxx",  // 这个可以用来邀请外部用户
    "user_id": "xxxxxx"
}
```

#### 方式 2: 调用 API 获取

```javascript
const response = await client.contact.user.get({
    path: { user_id: 'user_id_or_open_id' },
    params: { user_id_type: 'open_id' }
});
const unionId = response.data.user.union_id;
```

## API 使用方法

### 方法 1: 使用 createUnionChat（推荐）

```javascript
import { createChatManager } from './chat/index.js';

const chatManager = createChatManager(feishuClient);

const result = await chatManager.createUnionChat({
    name: '跨组织协作群',
    description: '与外部合作伙伴的协作群',
    member_list: [
        { open_id: 'ou_internal_user_1' },   // 内部用户
        { union_id: 'on_external_user_1' }   // 外部用户
    ]
});

console.log('群 ID:', result.chat_id);
```

### 方法 2: 使用 createChat

```javascript
const result = await chatManager.createChat({
    name: '跨组织项目群',
    description: '项目协作群',
    user_id_list: ['on_user_union_id_1', 'on_user_union_id_2'],
    user_id_type: 'union_id',
    chat_mode: 'group',
    chat_type: 'union'  // 关键：指定为联合群
});
```

## 完整示例

```javascript
import { createChatManager } from './chat/index.js';
import * as lark from '@larksuiteoapi/node-sdk';

// 1. 创建客户端
const client = new lark.Client({
    appId: process.env.FEISHU_APP_ID,
    appSecret: process.env.FEISHU_APP_SECRET
});

// 2. 创建群管理器
const chatManager = createChatManager(client);

// 3. 定义成员
const members = [
    { open_id: 'ou_internal_member_1' },     // 内部成员
    { open_id: 'ou_internal_member_2' },
    { union_id: 'on_external_member_1' },    // 外部成员
    { union_id: 'on_external_member_2' }
];

// 4. 创建外部群
try {
    const result = await chatManager.createUnionChat({
        name: '跨组织项目协作群',
        description: '与合作伙伴的项目协作群',
        member_list: members
    });
    
    console.log('✅ 外部群创建成功:');
    console.log('  群 ID:', result.chat_id);
    console.log('  群名称:', result.name);
} catch (error) {
    console.error('❌ 创建失败:', error.message);
    if (error.response?.data) {
        console.error('详细错误:', JSON.stringify(error.response.data, null, 2));
    }
}
```

## 常见错误处理

### 错误 1: 权限不足

```json
{
    "code": 99991663,
    "msg": "没有创建联合群聊的权限"
}
```

**解决方案**: 
- 在飞书开放平台申请 `im:union_chat` 权限
- 等待权限审核通过

### 错误 2: 企业未建立合作关系

```json
{
    "code": 99991664,
    "msg": "企业间未建立合作关系"
}
```

**解决方案**:
- 联系企业管理员
- 在飞书管理后台建立企业间合作关系

### 错误 3: 用户 ID 类型错误

```json
{
    "code": 99991665,
    "msg": "外部用户必须使用 union_id"
}
```

**解决方案**:
- 确保外部用户使用 `union_id` 而非 `open_id`
- 使用 `createUnionChat` 方法会自动处理

### 错误 4: 用户不存在

```json
{
    "code": 99991666,
    "msg": "用户不存在或未激活"
}
```

**解决方案**:
- 确认用户 ID 正确
- 确认用户已激活飞书账号
- 确认双方企业已建立合作关系

## 限制说明

| 限制项 | 说明 |
|--------|------|
| 人数上限 | 外部群人数上限约 500 人（内部群为 5000 人） |
| 权限要求 | 需要申请 `im:union_chat` 权限 |
| 企业合作 | 双方企业必须建立飞书商务合作关系 |
| 成员类型 | 外部成员必须使用 `union_id` |
| 创建者权限 | 通常需要企业管理员授权 |

## 最佳实践

### 1. 错误处理

```javascript
async function safeCreateUnionChat(options) {
    try {
        return await chatManager.createUnionChat(options);
    } catch (error) {
        // 记录详细错误信息
        console.error('创建外部群失败:', {
            code: error.response?.data?.code,
            message: error.message,
            details: error.response?.data
        });
        
        // 根据错误码提供解决方案
        const errorCode = error.response?.data?.code;
        switch (errorCode) {
            case 99991663:
                console.error('建议：申请 im:union_chat 权限');
                break;
            case 99991664:
                console.error('建议：建立企业合作关系');
                break;
            case 99991665:
                console.error('建议：使用 union_id 邀请外部用户');
                break;
        }
        
        throw error;
    }
}
```

### 2. ID 类型验证

```javascript
function validateMemberList(memberList) {
    return memberList.map(member => {
        const idTypes = ['open_id', 'union_id', 'user_id'];
        const usedTypes = idTypes.filter(type => member[type]);
        
        if (usedTypes.length === 0) {
            throw new Error(`成员缺少有效 ID: ${JSON.stringify(member)}`);
        }
        
        if (usedTypes.length > 1) {
            console.warn(`成员有多种 ID，将优先使用: ${usedTypes[0]}`);
        }
        
        return member;
    });
}
```

### 3. 成功后验证

```javascript
async function createAndVerifyUnionChat(options) {
    // 创建群聊
    const result = await chatManager.createUnionChat(options);
    
    // 验证群聊信息
    const chatInfo = await chatManager.getChatInfo(result.chat_id);
    console.log('群聊信息:', {
        id: chatInfo.chat_id,
        name: chatInfo.name,
        type: chatInfo.chat_type,
        memberCount: chatInfo.member_count
    });
    
    // 获取成员列表
    const members = await chatManager.getMembers(result.chat_id);
    console.log('成员数量:', members.members.length);
    
    return result;
}
```

## 测试脚本

运行测试：

```bash
cd E:\workspace\xpproject\agentSchool\plugins\feishu-bot

# 测试内部群创建
node create-union-chat.js

# 测试外部群创建（需要配置真实的 union_id）
# 编辑 create-union-chat.js，修改 EXTERNAL_USER.union_id 后运行
```

## 相关文档

- [飞书开放平台 - 创建群聊](https://open.feishu.cn/document/server-docs/im-v1/chat/create)
- [飞书开放平台 - 用户 ID 说明](https://open.feishu.cn/document/ukTMukTMukTM/uQjL0YDM4MjL5YjN)
- [飞书开放平台 - 企业合作](https://open.feishu.cn/document/ukTMukTMukTM/uEjL3YDM4MjL5YjN)