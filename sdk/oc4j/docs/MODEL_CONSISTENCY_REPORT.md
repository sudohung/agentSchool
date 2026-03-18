# Java SDK 实体类型与 openapi.json 一致性检查报告

## 检查日期
2026-03-18

## 检查范围
全面检查 Java SDK 所有模型类与 openapi.json 和 Python SDK 的字段定义一致性。

---

## 1. 发现的问题

### 1.1 高优先级问题

| 模型类 | 问题 | Python SDK | openapi.json |
|--------|------|------------|--------------|
| Todo.java | 多余字段 `createdAt` | ❌ 无此字段 | ❌ 无此字段 |
| Project.java | `icon` 使用 Map | ProjectIcon 强类型 | object |
| Project.java | `commands` 使用 Map | ProjectCommands 强类型 | object |
| Project.java | `time` 使用 Map | ProjectTime 强类型 | object |
| Agent.java | `permission` 使用 Map | PermissionRuleset 强类型 | PermissionRuleset |
| Agent.java | `model` 使用 Map | AgentModel 强类型 | object |

### 1.2 中优先级问题

| 模型类 | 问题 | 说明 |
|--------|------|------|
| TokenInfo.java | input/output 应为 required | Python SDK 定义为 required |
| Session.java | 缺少 workspaceID 注解 | 已正确使用 @JsonProperty |

---

## 2. 详细对比

### 2.1 Session ✅

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| id | string (required) | str | String | ✅ |
| slug | string (required) | str | String | ✅ |
| projectID | string (required) | str (@JsonProperty) | String (@JsonProperty) | ✅ |
| workspaceID | string (optional) | Optional[str] | String (@JsonProperty) | ✅ |
| directory | string (required) | str | String | ✅ |
| parentID | string (optional) | Optional[str] | String (@JsonProperty) | ✅ |
| title | string (required) | str | String | ✅ |
| version | string (required) | str | String | ✅ |
| time | object (required) | TimeInfo | TimeInfo | ✅ |
| permission | PermissionRuleset (optional) | Optional[Dict] | Map | ⚠️ 应用强类型 |
| summary | object (optional) | SessionSummary | SessionSummary | ✅ |
| share | object (optional) | ShareInfo | Map | ⚠️ 应用强类型 |
| revert | object (optional) | RevertInfo | Map | ⚠️ 应用强类型 |

### 2.2 Todo ⚠️

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| content | string (required) | str | String | ✅ |
| status | string (required) | enum | String | ⚠️ 应用 enum |
| priority | string (required) | enum | String | ⚠️ 应用 enum |
| id | - | Optional[str] | String | ✅ |
| createdAt | - | ❌ 无 | Long | ❌ 多余字段 |

### 2.3 Project ⚠️

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| id | string (required) | str | String | ✅ |
| worktree | string (required) | str | String (@JsonProperty) | ✅ |
| vcs | string (optional) | enum | String | ⚠️ 应用 enum |
| name | string (optional) | Optional[str] | String | ✅ |
| icon | object (optional) | ProjectIcon | Map | ❌ 应用强类型 |
| commands | object (optional) | ProjectCommands | Map | ❌ 应用强类型 |
| time | object (required) | ProjectTime | Map | ❌ 应用强类型 |
| sandboxes | List<string> (required) | List[str] | List<String> | ✅ |

### 2.4 Agent ⚠️

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| name | string (required) | str | String | ✅ |
| description | string (optional) | Optional[str] | String | ✅ |
| mode | enum (required) | enum | enum | ✅ |
| native | boolean (optional) | Optional[bool] | Boolean | ✅ |
| hidden | boolean (optional) | Optional[bool] | Boolean | ✅ |
| topP | number (optional) | Optional[float] | Double | ✅ |
| temperature | number (optional) | Optional[float] | Double | ✅ |
| color | string (optional) | Optional[str] | String | ✅ |
| permission | PermissionRuleset (required) | PermissionRuleset | Map | ❌ 应用强类型 |
| model | object (optional) | AgentModel | Map | ❌ 应用强类型 |
| variant | string (optional) | Optional[str] | String | ✅ |
| prompt | string (optional) | Optional[str] | String | ✅ |
| options | object (required) | Dict | Map | ✅ |
| steps | integer (optional) | Optional[int] | Integer | ✅ |

### 2.5 FileNode ✅

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| name | string (required) | str | String | ✅ |
| path | string (required) | str | String | ✅ |
| absolute | string (required) | str | String | ✅ |
| type | enum (required) | enum | enum | ✅ |
| ignored | boolean (required) | bool | Boolean | ✅ |

### 2.6 FileContent ✅

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| type | enum (required) | enum | enum | ✅ |
| content | string (required) | str | String | ✅ |
| diff | string (optional) | Optional[str] | String | ✅ |
| patch | object (optional) | Optional[Dict] | Object | ✅ |
| encoding | string (optional) | Optional[str] | String | ✅ |
| mimeType | string (optional) | Optional[str] | String | ✅ |

### 2.7 Provider ⚠️

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| id | string (required) | str | String | ✅ |
| name | string (required) | str | String | ✅ |
| source | enum (required) | enum | enum | ✅ |
| env | List<string> (required) | List[str] | List<String> | ✅ |
| key | string (optional) | Optional[str] | String | ✅ |
| options | object (required) | Dict | Map | ✅ |
| models | object (required) | Dict | Map | ⚠️ 应用强类型 |
| api | - | Optional[str] | String | ✅ |
| npm | - | Optional[str] | String | ✅ |

### 2.8 PermissionRequest ✅

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| id | string (required) | str | String | ✅ |
| sessionID | string (required) | str | String (@JsonProperty) | ✅ |
| permission | string (required) | str | String | ✅ |
| patterns | List<string> (required) | List[str] | List<String> | ✅ |
| metadata | object (required) | Dict | Map | ✅ |
| always | List<string> (required) | List[str] | List<String> | ✅ |
| tool | object (optional) | Optional[Dict] | PermissionToolRef | ✅ |

### 2.9 FileDiff ✅

| 字段 | openapi.json | Python SDK | Java SDK | 状态 |
|------|-------------|------------|----------|------|
| file | string (required) | str | String | ✅ |
| before | string (required) | str | String | ✅ |
| after | string (required) | str | String | ✅ |
| additions | number (required) | int | int | ✅ |
| deletions | number (required) | int | int | ✅ |
| status | enum (optional) | Optional[enum] | String | ⚠️ 应用 enum |

---

## 3. 需要创建的强类型类

### 3.1 Project 相关
- `ProjectTime` - created, updated, initialized
- `ProjectIcon` - url, override, color
- `ProjectCommands` - start

### 3.2 Agent 相关
- `AgentPermission` - permission, action, pattern
- `PermissionRuleset` - List<AgentPermission>
- `AgentModel` - providerID, modelID

### 3.3 Session 相关
- `ShareInfo` - url
- `RevertInfo` - messageID, partID, snapshot, diff

### 3.4 Todo 相关
- 添加 enum: `TodoStatus`, `TodoPriority`
- 删除多余字段 `createdAt`

---

## 4. 修复计划

### 阶段 1: 创建缺失的强类型类
1. 创建 ProjectTime, ProjectIcon, ProjectCommands
2. 创建 AgentPermission, PermissionRuleset, AgentModel
3. 创建 ShareInfo, RevertInfo

### 阶段 2: 更新现有模型类
1. 更新 Project.java 使用强类型
2. 更新 Agent.java 使用强类型
3. 更新 Session.java 使用强类型
4. 更新 Todo.java - 删除 createdAt, 添加 enum

### 阶段 3: 添加缺失的 enum
1. TodoStatus enum
2. TodoPriority enum
3. FileDiffStatus enum

---

## 5. 总结

| 类别 | 检查数量 | 一致 | 需修复 |
|------|---------|------|--------|
| 完全一致 | 15 个类 | 15 | 0 |
| 需要修复 | 6 个类 | - | 6 |
| 需要创建 | 7 个类 | - | 7 |

**总体一致性**: 约 70%

**修复后预期一致性**: 100%